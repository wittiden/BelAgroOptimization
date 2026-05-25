import pyomo.environ as pyo
from pyomo.environ import Constraint, Objective, maximize, Var, Binary
from pyomo.opt import SolverStatus, TerminationCondition
from loguru import logger


class BelarusAgroModel:
    """Оптимизационная модель с бинарными переменными (одно поле - одна культура в год)"""

    __slots__ = (
        'model', 'scenario_id', 'scenario_name', 'db_url',
        # Растениеводство
        'crops', 'all_crops', 'fields', 'years', 'field_area', 'total_land',
        'base_yield', 'price', 'cost', 'max_area_pct',
        'seed_cost', 'fert_response', 'max_fert', 'fert_cost', 'feed_types',
        # Животноводство
        'min_cows', 'max_cows', 'milk_price', 'milk_yield',
        'base_milk_yield', 'max_milk_yield', 'cow_cost_summer', 'cow_cost_winter',
        'energy_cost_cow_winter',
        'min_cattle', 'max_cattle', 'beef_price',
        'base_beef_yield', 'max_beef_yield', 'cattle_cost_summer', 'cattle_cost_winter',
        'energy_cost_cattle_winter',
        'min_pigs', 'max_pigs', 'pork_price',
        'base_pork_yield', 'max_pork_yield', 'pig_cost_summer', 'pig_cost_winter',
        'energy_cost_pig_winter',
        # Корма
        'feed_price_summer', 'feed_price_winter',
        'base_feed_need_summer', 'base_feed_need_winter',
        'max_feed', 'feed_efficiency', 'feed_output',
        'diminishing_beta',
        # Константы
        'summer_days', 'winter_days',
        'grain_min_pct', 'fallow_min_pct', 'feed_crop_min_pct',
        'potato_max_pct', 'rapeseed_max_pct',
        'seasonal_adjustment', 'winter_productivity_factor',
        # Погода
        'weather',
    )

    def __init__(self, model_data: dict, scenario_name: str = 'Базовый сценарий 2025'):
        self.model = pyo.ConcreteModel()
        self.db_url = None
        self.scenario_name = scenario_name
        self.scenario_id = None

        self.summer_days = 180
        self.winter_days = 185
        self.grain_min_pct = 0.35
        self.fallow_min_pct = 0.05

        self.crops = []
        self.all_crops = []
        self.fields = []
        self.years = []
        self.field_area = {}
        self.total_land = 0
        self.base_yield = {}
        self.price = {}
        self.cost = {}
        self.max_area_pct = {}
        self.seed_cost = {}
        self.fert_response = {}
        self.max_fert = 180.0
        self.fert_cost = 2.7
        self.feed_types = []

        self.min_cows = 0
        self.max_cows = 0
        self.milk_price = 0
        self.milk_yield = 0
        self.base_milk_yield = 0
        self.max_milk_yield = 0
        self.cow_cost_summer = 0
        self.cow_cost_winter = 0
        self.energy_cost_cow_winter = 0

        self.min_cattle = 0
        self.max_cattle = 0
        self.beef_price = 0
        self.base_beef_yield = 0
        self.max_beef_yield = 0
        self.cattle_cost_summer = 0
        self.cattle_cost_winter = 0
        self.energy_cost_cattle_winter = 0

        self.min_pigs = 0
        self.max_pigs = 0
        self.pork_price = 0
        self.base_pork_yield = 0
        self.max_pork_yield = 0
        self.pig_cost_summer = 0
        self.pig_cost_winter = 0
        self.energy_cost_pig_winter = 0

        self.feed_price_summer = {}
        self.feed_price_winter = {}
        self.base_feed_need_summer = {}
        self.base_feed_need_winter = {}
        self.max_feed = {}
        self.feed_efficiency = {}
        self.feed_output = {}
        self.diminishing_beta = {}

        self.weather = {}

        self._load_data_to_model(model_data)

    def _load_data_to_model(self, data: dict) -> None:
        """Загрузка данных из словаря в атрибуты модели"""

        for key, v in data.items():
            if key in self.__slots__:
                setattr(self, key, v)

        if self.crops and not self.all_crops:
            self.all_crops = list(set(self.crops + ['fallow']))

    def get_weather_factor(self, crop: str, year: int) -> float:
        """Расчёт погодного коэффициента"""

        weather = self.weather[year]
        temp = weather.temp
        rain = weather.rain

        # 550 мм осадков - норма Беларуси
        if rain >= 550:
            rain_factor = 1.0
        else:
            drought = (550 - rain) / 550
            sensitivity = {
                'winter_wheat': 0.30, 'spring_wheat': 0.35, 'barley': 0.30,
                'rapeseed': 0.45, 'potato': 0.50, 'sugar_beet': 0.40,
                'corn_silage': 0.42, 'grass': 0.38
            }
            rain_factor = 1 - drought * sensitivity.get(crop, 0.40)
            rain_factor = max(0.65, rain_factor)

        if crop.startswith('winter'):
            if temp <= 22:
                temp_factor = 1.0
            elif temp <= 28:
                temp_factor = 1 - 0.08 * (temp - 22)
            else:
                temp_factor = max(0.5, 1 - 0.12 * (temp - 22))
        else:
            if temp <= 20:
                temp_factor = 1.0
            elif temp <= 28:
                temp_factor = 1 - 0.10 * (temp - 20)
            else:
                temp_factor = max(0.5, 1 - 0.15 * (temp - 20))

        return rain_factor * temp_factor

    def build_model(self) -> None:
        """Построение модели"""

        m = self.model

        m.CROPS = pyo.Set(initialize=self.crops)
        m.FIELDS = pyo.Set(initialize=self.fields)
        m.YEARS = pyo.Set(initialize=self.years)

        m.crop_choice = Var(m.CROPS, m.FIELDS, m.YEARS, within=Binary)
        m.production = Var(m.CROPS, m.FIELDS, m.YEARS, bounds=(0, None))
        m.cows = Var(m.YEARS, bounds=(self.min_cows, self.max_cows), within=pyo.NonNegativeReals)

        def one_crop_per_field_rule(model, field, year):
            """На каждом поле в каждый год может быть только одна культура"""

            return sum(model.crop_choice[c, field, year] for c in m.CROPS) == 1

        m.OneCropPerField = Constraint(m.FIELDS, m.YEARS, rule=one_crop_per_field_rule)

        def production_rule(model, crop, field, year):
            """Связь производства с выбранной культурой"""

            if crop == 'fallow':
                return model.production[crop, field, year] == 0

            # Урожайность с учетом погоды
            yield_per_ha = self.base_yield.get(crop, 0) * self.get_weather_factor(crop, year)
            field_area = self.field_area[field]

            # Производство = урожайность * площадь поля * индикатор выбора культуры
            return model.production[crop, field, year] == yield_per_ha * field_area * model.crop_choice[
                crop, field, year]

        m.ProductionRule = Constraint(m.CROPS, m.FIELDS, m.YEARS, rule=production_rule)

        GRAIN_CROPS = ['winter_wheat', 'spring_wheat', 'barley']

        def grain_requirement_rule(model, year):
            """Ограничение на минимальную долю зерновых"""

            grain_area = sum(
                self.field_area[f] * model.crop_choice[c, f, year]
                for c in GRAIN_CROPS if c in model.CROPS
                for f in m.FIELDS
            )
            return grain_area >= self.total_land * self.grain_min_pct

        m.GrainRequirement = Constraint(m.YEARS, rule=grain_requirement_rule)

        def fallow_requirement_rule(model, year):
            """Ограничение на минимальную долю пара"""

            fallow_area = sum(
                self.field_area[f] * model.crop_choice['fallow', f, year]
                for f in model.FIELDS
            )
            return fallow_area >= self.total_land * self.fallow_min_pct

        m.FallowRequirement = Constraint(m.YEARS, rule=fallow_requirement_rule)

        def max_area_rule(model, crop, year):
            """Ограничение на максимальную площадь каждой культуры"""

            if crop == 'fallow' or crop not in self.max_area_pct:
                return pyo.Constraint.Skip

            total_crop_area = sum(
                self.field_area[f] * model.crop_choice[crop, f, year]
                for f in m.FIELDS
            )
            return total_crop_area <= self.total_land * self.max_area_pct[crop]

        m.MaxArea = Constraint(m.CROPS, m.YEARS, rule=max_area_rule)

        if len(self.years) >= 2:
            years_list = sorted(list(self.years))

            for i in range(len(years_list) - 1):
                year_prev = years_list[i]
                year_curr = years_list[i + 1]

                def no_repeat_rule(model, crop, field, yp=year_prev, yc=year_curr):
                    """Запрет на повтор культур (кроме трав и пара)"""

                    if crop in ('grass', 'fallow'):
                        return pyo.Constraint.Skip

                    # Нельзя сеять ту же культуру два года подряд
                    return model.crop_choice[crop, field, yp] + model.crop_choice[crop, field, yc] <= 1

                constraint_name = f'NoRepeatCrop_{year_prev}_{year_curr}'
                setattr(m, constraint_name, Constraint(m.CROPS, m.FIELDS, rule=no_repeat_rule))

            if 'potato' in self.crops:
                if len(years_list) >= 3:
                    for i in range(len(years_list) - 2):
                        y1 = years_list[i]
                        y2 = years_list[i + 1]
                        y3 = years_list[i + 2]

                        def potato_3year_rule(model, field, year1=y1, year2=y2, year3=y3):
                            """Картофель можно сажать не чаще 1 раза за 3 года на одном поле"""

                            if 'potato' not in model.CROPS:
                                return pyo.Constraint.Skip

                            return (model.crop_choice['potato', field, year1] +
                                    model.crop_choice['potato', field, year2] +
                                    model.crop_choice['potato', field, year3]) <= 1

                        constraint_name = f'PotatoRotation_{y1}_{y2}_{y3}'
                        setattr(m, constraint_name, Constraint(m.FIELDS, rule=potato_3year_rule))

        # ========== 3. ЦЕЛЕВАЯ ФУНКЦИЯ (ЛИНЕЙНАЯ) ==========
        def objective_rule(model):
            total_profit = 0

            # Прибыль от растениеводства (линейная)
            for year in model.YEARS:
                for field in model.FIELDS:
                    for crop in model.CROPS:
                        if crop == 'fallow':
                            continue

                        # Выручка от продажи (линейная от production)
                        revenue = self.price.get(crop, 0) * model.production[crop, field, year]

                        # Затраты на выращивание (линейная от crop_choice)
                        expenses = self.cost.get(crop, 0) * self.field_area[field] * model.crop_choice[
                            crop, field, year]

                        total_profit += revenue - expenses

            # Прибыль от животноводства (линейная)
            for year in model.YEARS:
                milk_revenue = self.milk_price * model.cows[year] * self.milk_yield / 1000
                cow_expenses = model.cows[year] * 2500
                total_profit += milk_revenue - cow_expenses

            return total_profit

        m.Objective = Objective(rule=objective_rule, sense=maximize)

    def solve(self) -> bool:
        """Решение модели"""
        self.build_model()

        try:
            logger.info("Запуск GLPK решателя...")
            solver = pyo.SolverFactory('glpk')

            results = solver.solve(self.model, tee=True)

            if (results.solver.status == SolverStatus.ok and
                    results.solver.termination_condition == TerminationCondition.optimal):
                logger.info("Оптимальное решение найдено с GLPK")
                return True
            elif results.solver.termination_condition == TerminationCondition.feasible:
                logger.warning("Найдено feasible решение с GLPK, но не оптимальное")
                return True
            else:
                logger.error(f"GLPK: {results.solver.termination_condition}")
                return False

        except Exception as e:
            logger.error(f"Ошибка GLPK: {e}")
            return False

    def print_results(self) -> None:
        """Вывод результатов"""
        m = self.model

        crop_names_ru = {
            'winter_wheat': 'Озимая пшеница', 'spring_wheat': 'Яровая пшеница',
            'barley': 'Ячмень', 'rapeseed': 'Рапс', 'potato': 'Картофель',
            'sugar_beet': 'Сахарная свёкла', 'corn_silage': 'Кукуруза силос',
            'grass': 'Травы', 'fallow': 'Пар'
        }

        print("\n" + "=" * 80)
        print("🌾 ОПТИМИЗАЦИЯ СЕЛЬСКОГО ХОЗЯЙСТВА БЕЛАРУСИ")
        print(f"   Сценарий: {self.scenario_name}")
        print("   Модель: одно поле - одна культура в год")
        print("=" * 80)

        # Сбор данных по годам
        for year in m.YEARS:
            year_val = pyo.value(year)
            weather = self.weather.get(year_val)

            print(f"\n{'─' * 80}")
            print(f"📅 ГОД {year_val}")
            if weather:
                print(f"🌡️  {weather.temp:.1f}°C | 💧 {weather.rain:.0f} мм")
            print(f"{'─' * 80}")

            # Поголовье
            cows = pyo.value(m.cows[year])
            print(f"\n🐄 ПОГОЛОВЬЕ КОРОВ: {cows:>8.0f} гол.")

            # Посевы по полям
            print(f"\n🌾 РАСПРЕДЕЛЕНИЕ ПО ПОЛЯМ:")
            total_area_by_crop = {}

            for field in m.FIELDS:
                field_area = self.field_area[field]
                for crop in m.CROPS:
                    crop_choice_val = pyo.value(m.crop_choice[crop, field, year])
                    if crop_choice_val is not None and crop_choice_val > 0.5:
                        crop_name = crop_names_ru.get(crop, crop)
                        print(f"   Поле {field:2} ({field_area:>6.1f} га) : {crop_name}")
                        total_area_by_crop[crop] = total_area_by_crop.get(crop, 0) + field_area

            # Итоги по культурам
            if total_area_by_crop:
                print(f"\n📊 ИТОГО ПО КУЛЬТУРАМ:")
                for crop, area in sorted(total_area_by_crop.items(), key=lambda x: -x[1]):
                    crop_name = crop_names_ru.get(crop, crop)
                    pct = area / self.total_land * 100
                    print(f"   {crop_name:20} : {area:>8.1f} га ({pct:>5.1f}%)")

        # Расчет прибыли
        print(f"\n{'=' * 80}")
        print("💰 ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'=' * 80}")

        total_profit = 0
        for year in m.YEARS:
            year_val = pyo.value(year)
            year_profit = 0

            crop_profit_detail = {}

            for field in m.FIELDS:
                for crop in m.CROPS:
                    if crop == 'fallow':
                        continue

                    crop_choice_val = pyo.value(m.crop_choice[crop, field, year])
                    if crop_choice_val is not None and crop_choice_val > 0.5:
                        production = pyo.value(m.production[crop, field, year])
                        revenue = self.price.get(crop, 0) * production if production else 0
                        expenses = self.cost.get(crop, 0) * self.field_area[field]
                        crop_profit = revenue - expenses
                        year_profit += crop_profit
                        crop_profit_detail[crop] = crop_profit_detail.get(crop, 0) + crop_profit

            # Вывод прибыли по культурам
            if crop_profit_detail:
                print(f"\n📅 ГОД {year_val} - РАСТЕНИЕВОДСТВО:")
                for crop, profit in sorted(crop_profit_detail.items(), key=lambda x: -x[1]):
                    crop_name = crop_names_ru.get(crop, crop)
                    print(f"   {crop_name:20} : {profit:>12,.0f} BYN")

            # Животноводство
            cows = pyo.value(m.cows[year])
            milk_revenue = self.milk_price * cows * self.milk_yield / 1000
            cow_expenses = cows * 2500
            livestock_profit = milk_revenue - cow_expenses

            print(f"\n   🐄 Животноводство (год {year_val}):")
            print(f"      Выручка от молока: {milk_revenue:>12,.0f} BYN")
            print(f"      Затраты на коров: {cow_expenses:>12,.0f} BYN")
            print(f"      Прибыль:          {livestock_profit:>12,.0f} BYN")

            year_profit += livestock_profit
            print(f"\n   {'─' * 40}")
            print(f"   ИТОГО за год {year_val}: {year_profit:>15,.0f} BYN")

            total_profit += year_profit

        print(f"\n{'=' * 80}")
        print(f"🏆 ОБЩАЯ ПРИБЫЛЬ ЗА ПЕРИОД: {total_profit:>15,.0f} BYN")
        print(f"💰 СРЕДНЕГОДОВАЯ ПРИБЫЛЬ:   {total_profit / len(list(m.YEARS)):>15,.0f} BYN")

        print("=" * 80)
