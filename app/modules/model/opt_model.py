import pyomo.environ as pyo
from pyomo.environ import Constraint, Objective, maximize, Var, Binary
from pyomo.opt import SolverStatus, TerminationCondition
from loguru import logger
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class BelarusAgroModel:
    """
    Оптимизационная модель сельского хозяйства Беларуси.

    Ключевые механизмы:
    - Бинарные переменные: одно поле — одна культура в год
    - Баланс кормов: производство кормов с полей покрывает потребность скота,
      дефицит закупается на рынке по рыночным ценам
    - Штраф картофеля: высокая трудоёмкость отражается через повышенный cost,
      жёсткое ограничение площади ≤ 18% и запрет повторного посева 3 года подряд
    - Климатические коэффициенты: урожайность и продуктивность скота меняются по годам
    - Запрет влагоёмких культур при засухе < 480 мм
    """

    __slots__ = (
        'model', 'scenario_id', 'scenario_name', 'db_url',
        'crops', 'all_crops', 'fields', 'years', 'field_area', 'total_land',
        'base_yield', 'price', 'cost', 'max_area_pct',
        'seed_cost', 'fert_response', 'max_fert', 'fert_cost', 'feed_types',
        'min_cows', 'max_cows', 'milk_price', 'milk_yield',
        'base_milk_yield', 'max_milk_yield', 'cow_cost_summer', 'cow_cost_winter',
        'energy_cost_cow_winter',
        'min_cattle', 'max_cattle', 'beef_price',
        'base_beef_yield', 'max_beef_yield', 'cattle_cost_summer', 'cattle_cost_winter',
        'energy_cost_cattle_winter',
        'min_pigs', 'max_pigs', 'pork_price',
        'base_pork_yield', 'max_pork_yield', 'pig_cost_summer', 'pig_cost_winter',
        'energy_cost_pig_winter',
        'feed_price_summer', 'feed_price_winter',
        'base_feed_need_summer', 'base_feed_need_winter',
        'max_feed', 'feed_efficiency', 'feed_output',
        'diminishing_beta',
        'summer_days', 'winter_days',
        'grain_min_pct', 'fallow_min_pct', 'feed_crop_min_pct',
        'potato_max_pct', 'rapeseed_max_pct',
        'seasonal_adjustment', 'winter_productivity_factor',
        'weather',
    )

    FEED_CROPS = ('barley', 'corn_silage', 'grass')
    CROP_FEED_OUTPUT = {
        'winter_wheat': {'hay': 0.08, 'concentrate': 0.45},
        'spring_wheat': {'hay': 0.08, 'concentrate': 0.45},
        'barley':       {'hay': 0.08, 'concentrate': 0.50},
        'rapeseed':     {'hay': 0.03, 'concentrate': 0.16},
        'potato':       {'silage': 0.10, 'concentrate': 0.03},
        'sugar_beet':   {'silage': 0.22},
        'corn_silage':  {'silage': 0.95},
        'grass':        {'silage': 0.20, 'hay': 0.65, 'pasture': 0.20},
    }

    # Потребность скота в кормах (центнер/голову/год) по типу корма.
    # Источник: feed_data из БД (cow_need, cattle_need, pig_need) × сезонный коэф.
    # Значения — базовые (летний период). Зимой × 1.4 (из mapper._feed_need).
    # Годовая потребность = среднее взвешенное по сезонам.
    FEED_NEED_PER_HEAD = {
        'cow':    {'silage': 22.0, 'hay': 8.0, 'concentrate': 5.0, 'pasture': 20.0},
        'cattle': {'silage': 16.0, 'hay': 6.0, 'concentrate': 4.0, 'pasture': 15.0},
        'pig':    {'silage':  0.0, 'hay': 0.0, 'concentrate': 3.5, 'pasture':  0.0},
    }

    # Штраф картофеля: дополнительные скрытые затраты на трудоёмкость на га
    POTATO_LABOR_PENALTY_PER_HA = 8000.0


    # Скрытые затраты животноводства (BYN/голову/год), не включённые в cost_summer/winter
    OVERHEAD_COST_PER_HEAD = {
        'cow':    3500.0,
        'cattle': 1500.0,
        'pig':     250.0,
    }

    def __init__(self, model_data: dict, scenario_name: str = 'Базовый сценарий 2025'):
        self.model = pyo.ConcreteModel()
        self.scenario_name = scenario_name

        self.summer_days = 180
        self.winter_days = 185
        self.grain_min_pct = 0.35
        self.fallow_min_pct = 0.05
        self.feed_crop_min_pct = 0.15

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
        self.feed_types = []

        self.min_cows = 0;   self.max_cows = 0
        self.milk_price = 0; self.milk_yield = 0
        self.base_milk_yield = 0; self.max_milk_yield = 0
        self.cow_cost_summer = 0; self.cow_cost_winter = 0
        self.energy_cost_cow_winter = 0

        self.min_cattle = 0; self.max_cattle = 0
        self.beef_price = 0; self.base_beef_yield = 0
        self.max_beef_yield = 0
        self.cattle_cost_summer = 0; self.cattle_cost_winter = 0
        self.energy_cost_cattle_winter = 0

        self.min_pigs = 0;   self.max_pigs = 0
        self.pork_price = 0; self.base_pork_yield = 0
        self.max_pork_yield = 0
        self.pig_cost_summer = 0; self.pig_cost_winter = 0
        self.energy_cost_pig_winter = 0

        self.feed_output = {}
        self.diminishing_beta = {}

        self.potato_max_pct = 0.18
        self.rapeseed_max_pct = 0.15

        self.weather = {}
        self.winter_productivity_factor = {'milk': 0.70, 'beef': 0.85, 'pork': 0.88}

        self._load_data_to_model(model_data)

    def _load_data_to_model(self, data: dict) -> None:
        for key, v in data.items():
            if key in self.__slots__:
                setattr(self, key, v)
        if self.crops and not self.all_crops:
            self.all_crops = list(set(self.crops + ['fallow']))

        if self.feed_output:
            for crop, feeds in self.feed_output.items():
                if feeds:
                    self.CROP_FEED_OUTPUT[crop] = feeds

        logger.info(f"Загружено культур: {len(self.crops)}, полей: {len(self.fields)}, лет: {len(self.years)}")
        logger.info(f"Штраф картофеля: +{self.POTATO_LABOR_PENALTY_PER_HA} BYN/га к базовым затратам")

    def get_weather_factor(self, crop: str, year: int) -> float:
        """Климатический коэффициент урожайности культуры в данном году"""

        w = self.weather[year]
        temp, rain = w.temp, w.rain

        # Базовое кол-во осадков 550 (идеально)
        if rain >= 550:
            rain_factor = 1.0
        else:
            drought = (550 - rain) / 550
            sensitivity = {
                'winter_wheat': 0.30, 'spring_wheat': 0.35, 'barley':     0.30,
                'rapeseed':     0.45, 'potato':       0.50, 'sugar_beet': 0.60,
                'corn_silage':  0.42, 'grass':        0.38,
            }
            rain_factor = max(0.65, 1 - drought * sensitivity.get(crop, 0.40))

        if crop.startswith('winter'):
            temp_factor = 1.0 if temp <= 22 else max(0.5, 1 - 0.08 * (temp - 22))
        else:
            temp_factor = 1.0 if temp <= 20 else max(0.5, 1 - 0.10 * (temp - 20))

        return rain_factor * temp_factor

    def get_livestock_weather_factors(self, year: int) -> dict:
        """
        Годовые коэффициенты продуктивности скота.
        Тепловой стресс снижает надой, засуха ухудшает качество кормов.
        """

        w = self.weather[year]
        temp, rain = w.temp, w.rain

        heat_stress_milk = 1.0 if temp <= 18 else max(0.80, 1.0 - 0.03 * (temp - 18.0))

        if rain >= 550:
            feed_q = 1.00
        elif rain >= 480:
            feed_q = 0.95
        elif rain >= 400:
            feed_q = 0.88
        else:
            feed_q = 0.82

        milk_f = heat_stress_milk * feed_q
        beef_f = (1.0 if temp <= 20 else max(0.85, 1.0 - 0.02 * (temp - 20.0))) * feed_q
        pork_f = 1.0 if temp <= 22 else max(0.92, 1.0 - 0.015 * (temp - 22.0))

        return {'milk': milk_f, 'beef': beef_f, 'pork': pork_f}

    def get_livestock_cost_factors(self, year: int) -> dict:
        """Коэффициенты затрат: холод → больше отопления, жара → вентиляция."""

        temp = self.weather[year].temp
        if 5.0 <= temp <= 9.0:
            cf = 1.0
        elif temp < 5.0:
            cf = 1.0 + 0.03 * (5.0 - temp)
        else:
            cf = 1.0 + 0.015 * (temp - 9.0)
        return {'cow': cf, 'cattle': cf, 'pig': cf}

    def _compute_livestock_costs(self, year: int) -> dict:
        """
        Годовые затраты на голову × климатический коэффициент года
        """

        base_cow    = self.cow_cost_summer    + self.cow_cost_winter    + self.energy_cost_cow_winter
        base_cattle = self.cattle_cost_summer + self.cattle_cost_winter + self.energy_cost_cattle_winter
        base_pig    = self.pig_cost_summer    + self.pig_cost_winter    + self.energy_cost_pig_winter

        # Добавляем overhead: амортизация, ветеринария, труд, здания
        # (не входят в cost_summer/cost_winter из БД)
        base_cow    += self.OVERHEAD_COST_PER_HEAD['cow']
        base_cattle += self.OVERHEAD_COST_PER_HEAD['cattle']
        base_pig    += self.OVERHEAD_COST_PER_HEAD['pig']

        cf = self.get_livestock_cost_factors(year)
        return {
            'cow':    base_cow    * cf['cow'],
            'cattle': base_cattle * cf['cattle'],
            'pig':    base_pig    * cf['pig'],
        }

    def _compute_feed_produced(self, year: int) -> dict:
        """Расчёт производства кормов с полей (центнеры)."""

        m = self.model
        feed_prod = dict.fromkeys(['silage', 'hay', 'concentrate', 'pasture'], 0)

        for crop in set(m.CROPS) - {'fallow'}:
            crop_feed = self.CROP_FEED_OUTPUT.get(crop)
            if not crop_feed:
                continue

            yield_ha = self.base_yield.get(crop, 0) * self.get_weather_factor(crop, year)

            for field in m.FIELDS:
                prod = yield_ha * self.field_area[field] * m.crop_choice[crop, field, year]
                for feed_type, ratio in crop_feed.items():
                    if feed_type in feed_prod:
                        feed_prod[feed_type] += prod * ratio * 10

        return feed_prod

    def _compute_feed_needed(self, year: int) -> dict:
        """
        Потребность скота в кормах (центнеров/год) по типу корма.

        Потребность = поголовье × норма (ц/голову/год).
        Зимняя норма × 1.4 (mapper._feed_need), итоговая — среднегодовая.
        """
        m = self.model
        # расчет доли дней
        ss = self.summer_days / (self.summer_days + self.winter_days)
        ws = self.winter_days  / (self.summer_days + self.winter_days)

        need = {ft: 0 for ft in ['silage', 'hay', 'concentrate', 'pasture']}

        ANIMALS = [('cow', 'cows'), ('cattle', 'cattle'), ('pig', 'pigs')]

        for animal, attr in ANIMALS:
            heads_var = getattr(m, attr)[year]
            for ft, base_need in self.FEED_NEED_PER_HEAD.get(animal, {}).items():
                if ft in need:
                    need[ft] += heads_var * base_need * (ss + 1.4 * ws)

        return need


    def build_model(self) -> None:
        m = self.model

        m.CROPS  = pyo.Set(initialize=self.crops)
        m.FIELDS = pyo.Set(initialize=self.fields)
        m.YEARS  = pyo.Set(initialize=self.years)

        m.crop_choice = Var(m.CROPS, m.FIELDS, m.YEARS, within=Binary)
        m.production  = Var(m.CROPS, m.FIELDS, m.YEARS, bounds=(0, None))

        m.cows   = Var(m.YEARS, bounds=(self.min_cows,   self.max_cows),   within=pyo.NonNegativeReals)
        m.cattle = Var(m.YEARS, bounds=(self.min_cattle, self.max_cattle), within=pyo.NonNegativeReals)
        m.pigs   = Var(m.YEARS, bounds=(self.min_pigs,   self.max_pigs),   within=pyo.NonNegativeReals)

        FEED_TYPES = ['silage', 'hay', 'concentrate', 'pasture']
        m.feed_purchase = Var(FEED_TYPES, m.YEARS, bounds=(0, None), within=pyo.NonNegativeReals)

        def one_crop_rule(model, field, year):
            """одна культура на поле"""

            return sum(model.crop_choice[c, field, year] for c in m.CROPS) == 1

        m.OneCropPerField = Constraint(m.FIELDS, m.YEARS, rule=one_crop_rule)

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

        def potato_area_rule(model, year):
            """картофель ≤ 18% (ограничение площади)"""

            return sum(
                self.field_area[f] * model.crop_choice['potato', f, year] for f in m.FIELDS
            ) <= self.total_land * self.potato_max_pct

        m.PotatoMaxArea = Constraint(m.YEARS, rule=potato_area_rule)

        PURCHASABLE = ['silage', 'hay', 'concentrate']

        def feed_balance_rule(model, feed_type, year):
            """
            Производство кормов с полей + закупка ≥ потребность скота.
            Закупка входит в целевую функцию как расход (по рыночной цене).
            Пастбище (pasture) нельзя купить — только с пастбищных угодий.
            """

            produced = self._compute_feed_produced(year).get(feed_type, 0)
            needed   = self._compute_feed_needed(year).get(feed_type, 0)

            if feed_type in PURCHASABLE:
                return produced + model.feed_purchase[feed_type, year] >= needed

            else:
                return produced >= needed * 0.6   # 60% потребности покрывается пастбищем, остальное — силосом

        m.FeedBalance = Constraint(FEED_TYPES, m.YEARS, rule=feed_balance_rule)


        if len(self.years) >= 2:
            years_list = sorted(list(self.years))

            for i in range(len(years_list) - 1):
                year_prev = years_list[i]
                year_curr = years_list[i + 1]

                def no_repeat_rule(model, crop, field, yp=year_prev, yc=year_curr):
                    """Запрет на повтор культур (кроме трав и пара)"""

                    if crop in ('grass', 'fallow'):
                        return pyo.Constraint.Skip

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


        def objective_rule(model):
            """Целевая функция"""

            total = 0

            for year in model.YEARS:
                year_val = pyo.value(year)
                wf = self.get_livestock_weather_factors(year_val)
                costs = self._compute_livestock_costs(year_val)

                total += sum(
                    # ВЫРУЧКА
                    self.price.get(crop, 0) * model.production[crop, field, year]
                    -
                    # ЗАТРАТЫ
                    (self.cost.get(crop, 0) + (self.POTATO_LABOR_PENALTY_PER_HA if crop == 'potato' else 0))
                    * self.field_area[field] * model.crop_choice[crop, field, year]
                    for field in model.FIELDS
                    for crop in model.CROPS if crop != 'fallow'
                )

                total += self.milk_price * model.cows[year] * (self.milk_yield * wf['milk']) - model.cows[year] * costs[
                    'cow']

                if self.max_cattle > 0 and self.beef_price > 0:
                    total += self.beef_price * model.cattle[year] * (self.base_beef_yield * wf['beef']) - model.cattle[
                        year] * costs['cattle']

                if self.max_pigs > 0 and self.pork_price > 0:
                    total += self.pork_price * model.pigs[year] * (self.base_pork_yield * wf['pork']) - model.pigs[
                        year] * costs['pig']

            return total

        m.Objective = Objective(rule=objective_rule, sense=maximize)


    def solve(self) -> bool | None:
        self.build_model()
        try:
            logger.info("Запуск GLPK решателя...")

            solver = pyo.SolverFactory('glpk')
            results = solver.solve(self.model, tee=True)

            if (results.solver.status == SolverStatus.ok and
                    results.solver.termination_condition == TerminationCondition.optimal):
                return True
            elif results.solver.termination_condition == TerminationCondition.feasible:
                return True

        except Exception as e:
            logger.error(f"Ошибка GLPK: {e}")
            return False


    def print_results(self) -> None:
        m = self.model

        ru = {
            'winter_wheat': 'Озимая пшеница', 'spring_wheat': 'Яровая пшеница',
            'barley':       'Ячмень',          'rapeseed':     'Рапс',
            'potato':       'Картофель',        'sugar_beet':   'Сахарная свёкла',
            'corn_silage':  'Кукуруза силос',   'grass':        'Травы',
            'fallow':       'Пар',
        }

        print("\n" + "=" * 80)
        print("🌾 ОПТИМИЗАЦИЯ СЕЛЬСКОГО ХОЗЯЙСТВА БЕЛАРУСИ")
        print(f"   Сценарий: {self.scenario_name}")
        print("=" * 80)

        for year in m.YEARS:
            yv  = int(pyo.value(year))
            w   = self.weather.get(yv)

            print(f"\n{'─'*80}")
            print(f"📅 ГОД {yv}")
            if w:
                print(f"🌡️  {w.temp:.1f}°C | 💧 {w.rain:.0f} мм")

            print(f"{'─'*80}")


            print(f"\n🌾 РАСПРЕДЕЛЕНИЕ ПО ПОЛЯМ:")
            area_by_crop = {}
            for field in m.FIELDS:
                fa = self.field_area[field]
                for crop in m.CROPS:
                    v = pyo.value(m.crop_choice[crop, field, year])
                    if v is not None and v > 0.5:
                        print(f"   Поле {field:6} ({fa:>6.1f} га) : {ru.get(crop, crop)}")
                        area_by_crop[crop] = area_by_crop.get(crop, 0) + fa

            if area_by_crop:
                print(f"\n📊 ИТОГО ПО КУЛЬТУРАМ:")
                for crop, area in sorted(area_by_crop.items(), key=lambda x: -x[1]):
                    pct = area / self.total_land * 100
                    print(f"   {ru.get(crop,crop):20} : {area:>8.1f} га ({pct:>5.1f}%)")

        print(f"\n{'='*80}")
        print("💰 ФИНАНСОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*80}")

        total_profit = 0
        for year in m.YEARS:
            yv = int(pyo.value(year))
            yr_profit = 0
            crop_det  = {}
            potato_penalty_total = 0

            for field in m.FIELDS:
                for crop in m.CROPS:
                    if crop == 'fallow':
                        continue
                    v = pyo.value(m.crop_choice[crop, field, year])
                    if v is not None and v > 0.5:
                        prod    = pyo.value(m.production[crop, field, year]) or 0
                        rev     = self.price.get(crop, 0) * prod
                        fa      = self.field_area[field]
                        base_c  = self.cost.get(crop, 0) * fa
                        penalty = self.POTATO_LABOR_PENALTY_PER_HA * fa if crop == 'potato' else 0
                        profit  = rev - base_c - penalty
                        yr_profit += profit
                        crop_det[crop] = crop_det.get(crop, 0) + profit
                        if crop == 'potato':
                            potato_penalty_total += penalty

            print("=" * 80)

            print(f"\n📅 ГОД {yv} - РАСТЕНИЕВОДСТВО:")
            for crop, profit in sorted(crop_det.items(), key=lambda x: -x[1]):
                print(f"   {ru.get(crop,crop):20} : {profit:>12,.0f}")

            wf    = self.get_livestock_weather_factors(yv)
            costs = self._compute_livestock_costs(yv)
            cows   = pyo.value(m.cows[year])
            cattle = pyo.value(m.cattle[year])
            pigs   = pyo.value(m.pigs[year])

            eff_milk = self.milk_yield * wf['milk']
            milk_rev = self.milk_price * cows * eff_milk
            cow_exp  = cows * costs['cow']
            milk_p   = milk_rev - cow_exp

            print(f"\n   🐄 Животноводство (год {yv}):")
            print(f"      Надой: {eff_milk:,.0f} кг/гол (×{wf['milk']:.3f}) | Затраты ×{self.get_livestock_cost_factors(yv)['cow']:.3f}")
            print(f"      Молоко:    {milk_rev:>12,.0f} - {cow_exp:>10,.0f} = {milk_p:>12,.0f} BYN")

            ls_profit = milk_p

            if self.max_cattle > 0 and cattle:
                eff_beef   = self.base_beef_yield * wf['beef']
                beef_rev   = self.beef_price * cattle * eff_beef
                cattle_exp = cattle * costs['cattle']
                beef_p     = beef_rev - cattle_exp
                ls_profit += beef_p
                print(f"      Говядина:  {beef_rev:>12,.0f} - {cattle_exp:>10,.0f} = {beef_p:>12,.0f} BYN")

            if self.max_pigs > 0 and pigs:
                eff_pork  = self.base_pork_yield * wf['pork']
                pork_rev  = self.pork_price * pigs * eff_pork
                pig_exp   = pigs * costs['pig']
                pork_p    = pork_rev - pig_exp
                ls_profit += pork_p
                print(f"      Свинина:   {pork_rev:>12,.0f} - {pig_exp:>10,.0f} = {pork_p:>12,.0f} BYN")


            print(f"      ИТОГО животноводство: {ls_profit:>12,.0f} BYN")

            yr_profit += ls_profit
            print(f"\n   {'─'*40}")
            print(f"   ИТОГО за год {yv}: {yr_profit:>15,.0f} BYN")
            total_profit += yr_profit

        print(f"\n{'='*80}")
        print(f"🏆 ОБЩАЯ ПРИБЫЛЬ ЗА ПЕРИОД: {total_profit:>15,.0f} BYN")
        print(f"💰 СРЕДНЕГОДОВАЯ ПРИБЫЛЬ:   {total_profit / len(list(m.YEARS)):>15,.0f} BYN")
        print("=" * 80)

    def create_plots(self, output_dir: str = './plots') -> None:
        """
        Создание графиков по результатам оптимизации.

        Графики:
        1. Прибыль по годам (растениеводство, животноводство, общая)
        2. Распределение культур по годам (%)
        3. Прибыль от растениеводства по культурам (по годам)
        4. Прибыль от животноводства по видам
        5. Сводная таблица прибыли
        """

        # Создаём директорию для графиков (очищаем старые)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Удаляем старые PNG файлы
        for old_file in Path(output_dir).glob('*.png'):
            old_file.unlink()
        logger.info(f"Очищена папка {output_dir} от старых графиков")

        # Настройка стиля для чёрного фона
        plt.style.use('dark_background')
        plt.rcParams.update({
            'figure.facecolor': 'black',
            'axes.facecolor': '#1a1a1a',
            'savefig.facecolor': 'black',
            'axes.edgecolor': 'white',
            'axes.labelcolor': 'white',
            'text.color': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'legend.facecolor': '#1a1a1a',
            'legend.edgecolor': 'white',
            'grid.color': '#444444'
        })

        m = self.model
        years = sorted([int(pyo.value(y)) for y in m.YEARS])

        # Собираем данные
        crop_profit_by_year = {year: {} for year in years}
        livestock_profit_by_year = {year: {'cow': 0, 'cattle': 0, 'pig': 0} for year in years}
        total_profit_by_year = {year: 0 for year in years}
        crop_area_by_year = {year: {} for year in years}

        for year in years:
            # Растениеводство
            yr_crop_profit = 0
            for field in m.FIELDS:
                for crop in m.CROPS:
                    if crop == 'fallow':
                        continue
                    v = pyo.value(m.crop_choice[crop, field, year])
                    if v is not None and v > 0.5:
                        prod = pyo.value(m.production[crop, field, year]) or 0
                        rev = self.price.get(crop, 0) * prod
                        fa = self.field_area[field]
                        base_c = self.cost.get(crop, 0) * fa
                        penalty = self.POTATO_LABOR_PENALTY_PER_HA * fa if crop == 'potato' else 0
                        profit = rev - base_c - penalty
                        yr_crop_profit += profit
                        crop_profit_by_year[year][crop] = crop_profit_by_year[year].get(crop, 0) + profit

                        # Площади
                        crop_area_by_year[year][crop] = crop_area_by_year[year].get(crop, 0) + fa

            # Животноводство
            wf = self.get_livestock_weather_factors(year)
            costs = self._compute_livestock_costs(year)

            cows = pyo.value(m.cows[year])
            cattle = pyo.value(m.cattle[year])
            pigs = pyo.value(m.pigs[year])

            if cows:
                milk_rev = self.milk_price * cows * (self.milk_yield * wf['milk'])
                cow_exp = cows * costs['cow']
                livestock_profit_by_year[year]['cow'] = milk_rev - cow_exp

            if cattle and self.max_cattle > 0 and self.beef_price > 0:
                beef_rev = self.beef_price * cattle * (self.base_beef_yield * wf['beef'])
                cattle_exp = cattle * costs['cattle']
                livestock_profit_by_year[year]['cattle'] = beef_rev - cattle_exp

            if pigs and self.max_pigs > 0 and self.pork_price > 0:
                pork_rev = self.pork_price * pigs * (self.base_pork_yield * wf['pork'])
                pig_exp = pigs * costs['pig']
                livestock_profit_by_year[year]['pig'] = pork_rev - pig_exp

            total_profit_by_year[year] = yr_crop_profit + sum(livestock_profit_by_year[year].values())

        # ==================== ГРАФИК 1: Прибыль по годам ====================
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(years))
        width = 0.25

        crop_totals = [sum(crop_profit_by_year[y].values()) for y in years]
        livestock_totals = [sum(livestock_profit_by_year[y].values()) for y in years]
        total_totals = [total_profit_by_year[y] for y in years]

        bars1 = ax.bar(x - width, crop_totals, width, label='Растениеводство', color='#2ecc71', alpha=0.8)
        bars2 = ax.bar(x, livestock_totals, width, label='Животноводство', color='#3498db', alpha=0.8)
        bars3 = ax.bar(x + width, total_totals, width, label='Общая прибыль', color='#f1c40f', alpha=0.8)

        ax.set_xlabel('Год', fontsize=12, color='white')
        ax.set_ylabel('Прибыль (BYN)', fontsize=12, color='white')
        ax.set_title(f'Прибыль по годам - {self.scenario_name}', fontsize=14, color='white')
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Добавляем значения на столбцы
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:,.0f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=8, color='white')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/profit_by_year.png', dpi=150, bbox_inches='tight', facecolor='black')
        plt.close()
        logger.info(f"Сохранён график: {output_dir}/profit_by_year.png")

        # ==================== ГРАФИК 2: Распределение культур по годам (%) ====================
        fig, axes = plt.subplots(1, len(years), figsize=(6 * len(years), 6))
        if len(years) == 1:
            axes = [axes]

        ru_names = {
            'winter_wheat': 'Оз. пшеница', 'spring_wheat': 'Яр. пшеница',
            'barley': 'Ячмень', 'rapeseed': 'Рапс',
            'potato': 'Картофель', 'sugar_beet': 'Сах. свёкла',
            'corn_silage': 'Кукуруза', 'grass': 'Травы',
            'fallow': 'Пар'
        }

        for idx, year in enumerate(years):
            ax = axes[idx]
            areas = crop_area_by_year[year]
            if areas:
                sorted_items = sorted(areas.items(), key=lambda x: -x[1])
                crops = [ru_names.get(c, c) for c, _ in sorted_items]
                values = [v for _, v in sorted_items]
                colors = plt.cm.Set3(np.linspace(0, 1, len(crops)))

                wedges, texts, autotexts = ax.pie(values, labels=crops, autopct='%1.1f%%',
                                                  colors=colors, startangle=90, textprops={'color': 'white'})
                for autotext in autotexts:
                    autotext.set_color('white')
                ax.set_title(f'{year} год\nВсего: {self.total_land:.0f} га', fontsize=12, color='white')

        plt.suptitle(f'Распределение посевных площадей по годам - {self.scenario_name}', fontsize=14, color='white')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/crop_distribution.png', dpi=150, bbox_inches='tight', facecolor='black')
        plt.close()
        logger.info(f"Сохранён график: {output_dir}/crop_distribution.png")

        # ==================== ГРАФИК 3: Прибыль от растениеводства по культурам ====================
        fig, ax = plt.subplots(figsize=(12, 6))

        # Собираем все культуры, которые были за весь период
        all_crops = set()
        for year in years:
            all_crops.update(crop_profit_by_year[year].keys())
        all_crops = sorted(all_crops)

        # Данные для группировки
        x = np.arange(len(years))
        width = 0.8 / len(all_crops) if all_crops else 0.1
        colors = plt.cm.tab20(np.linspace(0, 1, len(all_crops)))

        bottom = np.zeros(len(years))
        for idx, crop in enumerate(all_crops):
            values = [crop_profit_by_year[y].get(crop, 0) for y in years]
            bars = ax.bar(x, values, width, bottom=bottom, label=ru_names.get(crop, crop), color=colors[idx])
            bottom += values

        ax.set_xlabel('Год', fontsize=12, color='white')
        ax.set_ylabel('Прибыль от растениеводства (BYN)', fontsize=12, color='white')
        ax.set_title(f'Прибыль от растениеводства по культурам - {self.scenario_name}', fontsize=14, color='white')
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/crop_profit_breakdown.png', dpi=150, bbox_inches='tight', facecolor='black')
        plt.close()
        logger.info(f"Сохранён график: {output_dir}/crop_profit_breakdown.png")

        # ==================== ГРАФИК 4: Прибыль от животноводства по видам ====================
        fig, ax = plt.subplots(figsize=(10, 6))

        cow_profit = [livestock_profit_by_year[y]['cow'] for y in years]
        cattle_profit = [livestock_profit_by_year[y]['cattle'] for y in years]
        pig_profit = [livestock_profit_by_year[y]['pig'] for y in years]

        x = np.arange(len(years))
        width = 0.25

        bars1 = ax.bar(x - width, cow_profit, width, label='Молоко', color='#5dade2', alpha=0.8)
        bars2 = ax.bar(x, cattle_profit, width, label='Говядина', color='#2ecc71', alpha=0.8)
        bars3 = ax.bar(x + width, pig_profit, width, label='Свинина', color='#e74c3c', alpha=0.8)

        ax.set_xlabel('Год', fontsize=12, color='white')
        ax.set_ylabel('Прибыль (BYN)', fontsize=12, color='white')
        ax.set_title(f'Прибыль от животноводства по видам - {self.scenario_name}', fontsize=14, color='white')
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.legend()
        ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/livestock_profit_breakdown.png', dpi=150, bbox_inches='tight', facecolor='black')
        plt.close()
        logger.info(f"Сохранён график: {output_dir}/livestock_profit_breakdown.png")

        # ==================== ГРАФИК 5: Сводная таблица прибыли ====================
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('tight')
        ax.axis('off')

        table_data = []
        for year in years:
            crop_total = sum(crop_profit_by_year[year].values())
            livestock_total = sum(livestock_profit_by_year[year].values())
            table_data.append(
                [year, f'{crop_total:,.0f}', f'{livestock_total:,.0f}', f'{total_profit_by_year[year]:,.0f}'])

        # Добавляем итоговую строку
        total_crop = sum(sum(crop_profit_by_year[y].values()) for y in years)
        total_livestock = sum(sum(livestock_profit_by_year[y].values()) for y in years)
        total_all = total_crop + total_livestock
        table_data.append(['ИТОГО', f'{total_crop:,.0f}', f'{total_livestock:,.0f}', f'{total_all:,.0f}'])

        columns = ['Год', 'Растениеводство', 'Животноводство', 'ИТОГО']
        table = ax.table(cellText=table_data, colLabels=columns, cellLoc='right', loc='center',
                         colWidths=[0.1, 0.3, 0.3, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)

        # Стилизация таблицы для тёмного фона
        for (row, col), cell in table.get_celld().items():
            cell.set_facecolor('#1a1a1a')
            cell.set_text_props(color='white')
            if row == 0:
                cell.set_facecolor('#2c2c2c')
                cell.set_text_props(color='white', fontweight='bold')

        ax.set_title(f'Сводная таблица прибыли - {self.scenario_name}', fontsize=14, color='white', pad=20)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/profit_summary_table.png', dpi=150, bbox_inches='tight', facecolor='black')
        plt.close()
        logger.info(f"Сохранён график: {output_dir}/profit_summary_table.png")

        print(f"\n📊 Все графики сохранены в папку: {output_dir}/")
        print(f"   - profit_by_year.png - Прибыль по годам")
        print(f"   - crop_distribution.png - Распределение культур")
        print(f"   - crop_profit_breakdown.png - Прибыль от культур")
        print(f"   - livestock_profit_breakdown.png - Прибыль от животноводства")
        print(f"   - profit_summary_table.png - Сводная таблица")
