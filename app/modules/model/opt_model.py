import pyomo.environ as pyo
from pyomo.environ import value, exp, Constraint, Objective, maximize, Var, Model
from pyomo.opt import SolverStatus, TerminationCondition
from typing import Any
from loguru import logger
import matplotlib.pyplot as plt
import numpy as np


class BelarusAgroModel:
    """Оптимизационная модель с загрузкой данных из репозитория"""

    __slots__ = (
        'model', 'data',
        #Растениеводство
        'crops', 'fields', 'years', 'field_area', 'total_land',
        'base_yield', 'price', 'cost', 'seed_cost', 'fert_response',
        'max_fert', 'fert_cost',
        #Животноводство
        'min_cows', 'max_cows', 'min_cattle', 'max_cattle', 'min_pigs', 'max_pigs',
        'base_milk_yield', 'base_beef_yield', 'base_pork_yield',
        'max_milk_yield', 'max_beef_yield', 'max_pork_yield',
        'milk_price', 'beef_price', 'pork_price',
        'cow_cost_summer', 'cow_cost_winter',
        'cattle_cost_summer', 'cattle_cost_winter',
        'pig_cost_summer', 'pig_cost_winter',
        'energy_cost_cow_winter', 'energy_cost_cattle_winter', 'energy_cost_pig_winter',
        #Корма
        'feed_types', 'feed_price_summer', 'feed_price_winter',
        'base_feed_need_summer', 'base_feed_need_winter',
        'max_feed', 'feed_efficiency', 'diminishing_beta', 'feed_output',
        #Константы
        'summer_days', 'winter_days', 'winter_productivity_factor',
        'grain_min_pct', 'feed_crop_min_pct', 'fallow_min_pct',
        'potato_max_pct', 'rapeseed_max_pct', 'seasonal_adjustment',
        #Погода
        'weather'
    )

    def __init__(self, data: dict[str, Any]) -> None:
        self.model: pyo.ConcreteModel = pyo.ConcreteModel()
        self.data: dict[str, Any] = data
        self._load_data_to_model()

    def _load_data_to_model(self) -> None:
        """Загрузка данных из словаря в атрибуты модели"""

        for key, v in self.data.items():
            if key in self.__slots__:
                setattr(self, key, v)
            else:
                print(f"Ключ '{key}' пропущен")

    def get_weather_factor(self, crop: str, year: int) -> float:
        """Расчёт погодного коэффициента"""

        weather_data = self.weather[year]

        rain_monthly = weather_data['rain']
        if rain_monthly < 100:
            rain_yearly = rain_monthly * 12
        else:
            rain_yearly = rain_monthly

        temp = weather_data['temp']

        sensitivity = {
            'winter_wheat': 0.30, 'spring_wheat': 0.35, 'barley': 0.30,
            'rapeseed': 0.45, 'potato': 0.50, 'sugar_beet': 0.40,
            'corn_silage': 0.42, 'grass': 0.38, 'fallow': 0
        }

        # Фактор осадков
        if rain_yearly >= 550:
            rain_factor = 1.0
        else:
            drought = (550 - rain_yearly) / 550
            rain_factor = 1 - drought * sensitivity.get(crop, 0.40)
            rain_factor = max(0.65, rain_factor)

        if rain_yearly < 500:
            if crop == 'potato':
                rain_factor *= 0.70  # картофель теряет ещё 30%
            elif crop == 'sugar_beet':
                rain_factor *= 0.75  # свёкла теряет ещё 25%
            elif crop == 'corn_silage':
                rain_factor *= 0.85  # кукуруза теряет ещё 15%
            elif crop == 'rapeseed':
                rain_factor *= 0.80  # рапс теряет ещё 20%

        elif rain_yearly < 450:  # сильная засуха
            if crop == 'potato':
                rain_factor *= 0.55
            elif crop == 'sugar_beet':
                rain_factor *= 0.60
            elif crop == 'corn_silage':
                rain_factor *= 0.75

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

        temp_factor = max(0.6, temp_factor)

        return rain_factor * temp_factor

    def build_model(self) -> None:
        """Построение модели Pyomo"""

        m: Model = self.model

        #оси
        m.C = pyo.Set(initialize=self.crops)
        m.F = pyo.Set(initialize=self.fields)
        m.Y = pyo.Set(initialize=self.years)
        m.FEED = pyo.Set(initialize=self.feed_types)

        #переменные, bounds - ограничения
        m.area = Var(m.C, m.F, m.Y, bounds=(0, None))
        m.production = Var(m.C, m.F, m.Y, bounds=(0, None))
        m.fert = Var(m.F, m.Y, bounds=(0, self.max_fert))
        m.feed_prod = Var(m.Y, m.FEED, bounds=(0, None))

        m.cows = Var(m.Y, bounds=(self.min_cows, self.max_cows))
        m.cattle = Var(m.Y, bounds=(self.min_cattle, self.max_cattle))
        m.pigs = Var(m.Y, bounds=(self.min_pigs, self.max_pigs))

        m.cow_feed_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.cow_feed_winter = Var(m.Y, m.FEED, bounds=(0, None))
        m.cattle_feed_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.cattle_feed_winter = Var(m.Y, m.FEED, bounds=(0, None))
        m.pig_feed_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.pig_feed_winter = Var(m.Y, m.FEED, bounds=(0, None))

        m.extra_cow_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.extra_cow_winter = Var(m.Y, m.FEED, bounds=(0, None))
        m.extra_cattle_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.extra_cattle_winter = Var(m.Y, m.FEED, bounds=(0, None))
        m.extra_pig_summer = Var(m.Y, m.FEED, bounds=(0, None))
        m.extra_pig_winter = Var(m.Y, m.FEED, bounds=(0, None))

        m.milk_yield_summer = Var(m.Y, bounds=(self.base_milk_yield * 0.9, self.max_milk_yield))
        m.milk_yield_winter = Var(m.Y, bounds=(self.base_milk_yield * 0.7, self.max_milk_yield * 0.85))
        m.beef_yield_summer = Var(m.Y, bounds=(0, None))
        m.beef_yield_winter = Var(m.Y, bounds=(0, None))
        m.pork_yield_summer = Var(m.Y, bounds=(0, None))
        m.pork_yield_winter = Var(m.Y, bounds=(0, None))

        def land_rule(m: Model, f, y):
            """Сумма площади под культуры в год не больше самого поля"""

            return sum(m.area[c, f, y] for c in m.C) <= self.field_area[f] #type: ignore

        m.land_limit = Constraint(m.F, m.Y, rule=land_rule)

        def grain_rule(m: Model, y):
            """Суммарная площадь пшеницы больше min_pct (>35%)"""

            grain = sum(
                m.area['winter_wheat', f, y] +
                m.area['spring_wheat', f, y] +
                m.area['barley', f, y]
                for f in m.F
            )
            return grain >= self.total_land * self.grain_min_pct

        m.grain_rule = Constraint(m.Y, rule=grain_rule)

        def feed_crop_rule(m: Model, y):
            """Суммарная площадь кормовых больше min_pct (>20%)"""

            feed_area = sum(
                m.area['corn_silage', f, y] +
                m.area['grass', f, y]
                for f in m.F
            )
            return feed_area >= self.total_land * self.feed_crop_min_pct

        m.feed_crop_rule = Constraint(m.Y, rule=feed_crop_rule)

        def fallow_rule(m: Model, y):
            """Суммарная площадь отдыхающих полей больше min_pct (>5%)"""

            fallow_area = sum(m.area['fallow', f, y] for f in m.F) #type: ignore
            return fallow_area >= self.total_land * self.fallow_min_pct

        m.fallow_rule = Constraint(m.Y, rule=fallow_rule)

        def potato_rule(m: Model, y):
            """Ограничение на максимальную площадь картошки"""

            return sum(m.area['potato', f, y] for f in m.F) <= self.total_land * self.potato_max_pct #type: ignore

        m.potato_rule = Constraint(m.Y, rule=potato_rule)

        def rape_rule(m: Model, y):
            """Ограничение на максимальную площадь рапса"""

            return sum(m.area['rapeseed', f, y] for f in m.F) <= self.total_land * self.rapeseed_max_pct #type: ignore

        m.rape_rule = Constraint(m.Y, rule=rape_rule)

        def prod_rule(m: Model, c, f, y):
            """Расчёт урожайности: (базовая + эффект удобрений) × погодный фактор"""

            wf = self.get_weather_factor(c, y)
            fert_effect = (self.fert_response[c] * m.fert[f, y]) / (1 + 0.015 * m.fert[f, y]) #type: ignore
            yield_per_ha = (self.base_yield[c] + fert_effect) * wf
            return m.production[c, f, y] == yield_per_ha * m.area[c, f, y] #type: ignore

        m.prod_rule = Constraint(m.C, m.F, m.Y, rule=prod_rule)

        def feed_prod_rule(m: Model, y, ft):
            """Производство кормов = сумма по культурам: урожай × коэффициент выхода корма"""

            return m.feed_prod[y, ft] == sum(
                m.production[c, f, y] * self.feed_output.get(c, {}).get(ft, 0)
                for c in m.C for f in m.F
            )

        m.feed_prod_rule = Constraint(m.Y, m.FEED, rule=feed_prod_rule)

        def extra_cow_summer_rule(m: Model, y, ft):
            """Дополнительное летнее кормление коров = фактическое − норма"""

            need = self.base_feed_need_summer.get('cow', {}).get(ft, 0)
            return m.extra_cow_summer[y, ft] >= m.cow_feed_summer[y, ft] - need

        m.extra_cow_summer_rule = Constraint(m.Y, m.FEED, rule=extra_cow_summer_rule)

        def extra_cow_winter_rule(m: Model, y, ft):
            """Дополнительное зимнее кормление коров = фактическое − норма (зимой норма выше)"""

            need = self.base_feed_need_winter.get('cow', {}).get(ft, 0)
            return m.extra_cow_winter[y, ft] >= m.cow_feed_winter[y, ft] - need

        m.extra_cow_winter_rule = Constraint(m.Y, m.FEED, rule=extra_cow_winter_rule)

        def extra_cattle_summer_rule(m: Model, y, ft):
            """Дополнительное летнее кормление КРС = фактическое − норма"""

            need = self.base_feed_need_summer.get('cattle', {}).get(ft, 0)
            return m.extra_cattle_summer[y, ft] >= m.cattle_feed_summer[y, ft] - need

        m.extra_cattle_summer_rule = Constraint(m.Y, m.FEED, rule=extra_cattle_summer_rule)

        def extra_cattle_winter_rule(m: Model, y, ft):
            """Дополнительное зимнее кормление КРС = фактическое − норма (зимой норма выше)"""

            need = self.base_feed_need_winter.get('cattle', {}).get(ft, 0)
            return m.extra_cattle_winter[y, ft] >= m.cattle_feed_winter[y, ft] - need

        m.extra_cattle_winter_rule = Constraint(m.Y, m.FEED, rule=extra_cattle_winter_rule)

        def extra_pig_summer_rule(m: Model, y, ft):
            """Дополнительное летнее кормление свиней = фактическое − норма"""

            need = self.base_feed_need_summer.get('pig', {}).get(ft, 0)
            return m.extra_pig_summer[y, ft] >= m.pig_feed_summer[y, ft] - need

        m.extra_pig_summer_rule = Constraint(m.Y, m.FEED, rule=extra_pig_summer_rule)

        def extra_pig_winter_rule(m: Model, y, ft):
            """Дополнительное зимнее кормление свиней = фактическое − норма (зимой норма выше)"""

            need = self.base_feed_need_winter.get('pig', {}).get(ft, 0)
            return m.extra_pig_winter[y, ft] >= m.pig_feed_winter[y, ft] - need

        m.extra_pig_winter_rule = Constraint(m.Y, m.FEED, rule=extra_pig_winter_rule)

        def min_cow_summer_rule(m: Model, y, ft):
            """Минимальное летнее кормление коров: не ниже нормы"""

            need = self.base_feed_need_summer.get('cow', {}).get(ft, 0)
            return m.cow_feed_summer[y, ft] >= need

        m.min_cow_summer = Constraint(m.Y, m.FEED, rule=min_cow_summer_rule)

        def min_cow_winter_rule(m: Model, y, ft):
            """Минимальное зимнее кормление коров: не ниже повышенной зимней нормы"""

            need = self.base_feed_need_winter.get('cow', {}).get(ft, 0)
            return m.cow_feed_winter[y, ft] >= need

        m.min_cow_winter = Constraint(m.Y, m.FEED, rule=min_cow_winter_rule)

        def min_cattle_summer_rule(m: Model, y, ft):
            """Минимальное летнее кормление КРС: не ниже нормы"""

            need = self.base_feed_need_summer.get('cattle', {}).get(ft, 0)
            return m.cattle_feed_summer[y, ft] >= need

        m.min_cattle_summer = Constraint(m.Y, m.FEED, rule=min_cattle_summer_rule)

        def min_cattle_winter_rule(m: Model, y, ft):
            """Минимальное зимнее кормление КРС: не ниже повышенной зимней нормы"""

            need = self.base_feed_need_winter.get('cattle', {}).get(ft, 0)
            return m.cattle_feed_winter[y, ft] >= need

        m.min_cattle_winter = Constraint(m.Y, m.FEED, rule=min_cattle_winter_rule)

        def min_pig_summer_rule(m: Model, y, ft):
            """Минимальное летнее кормление свиней: не ниже нормы"""

            need = self.base_feed_need_summer.get('pig', {}).get(ft, 0)
            return m.pig_feed_summer[y, ft] >= need

        m.min_pig_summer = Constraint(m.Y, m.FEED, rule=min_pig_summer_rule)

        def min_pig_winter_rule(m: Model, y, ft):
            """Минимальное зимнее кормление свиней: не ниже повышенной зимней нормы"""

            need = self.base_feed_need_winter.get('pig', {}).get(ft, 0)
            return m.pig_feed_winter[y, ft] >= need

        m.min_pig_winter = Constraint(m.Y, m.FEED, rule=min_pig_winter_rule)

        def max_cow_summer_rule(m: Model, y, ft):
            """Максимальное летнее кормление коров: не выше физиологического предела"""

            limit = self.max_feed.get('cow', {}).get(ft, 100.0)
            return m.cow_feed_summer[y, ft] <= limit

        m.max_cow_summer = Constraint(m.Y, m.FEED, rule=max_cow_summer_rule)

        def max_cow_winter_rule(m: Model, y, ft):
            """Максимальное зимнее кормление коров: не выше физиологического предела"""

            limit = self.max_feed.get('cow', {}).get(ft, 100.0)
            return m.cow_feed_winter[y, ft] <= limit

        m.max_cow_winter = Constraint(m.Y, m.FEED, rule=max_cow_winter_rule)

        def max_cattle_summer_rule(m: Model, y, ft):
            """Максимальное летнее кормление КРС: не выше физиологического предела"""

            limit = self.max_feed.get('cattle', {}).get(ft, 80.0)
            return m.cattle_feed_summer[y, ft] <= limit

        m.max_cattle_summer = Constraint(m.Y, m.FEED, rule=max_cattle_summer_rule)

        def max_cattle_winter_rule(m: Model, y, ft):
            """Максимальное зимнее кормление КРС: не выше физиологического предела"""

            limit = self.max_feed.get('cattle', {}).get(ft, 80.0)
            return m.cattle_feed_winter[y, ft] <= limit

        m.max_cattle_winter = Constraint(m.Y, m.FEED, rule=max_cattle_winter_rule)

        def max_pig_summer_rule(m: Model, y, ft):
            """Максимальное летнее кормление свиней: не выше предела"""

            limit = self.max_feed.get('pig', {}).get(ft, 50.0)
            return m.pig_feed_summer[y, ft] <= limit

        m.max_pig_summer = Constraint(m.Y, m.FEED, rule=max_pig_summer_rule)

        def max_pig_winter_rule(m: Model, y, ft):
            """Максимальное зимнее кормление свиней: не выше предела"""

            limit = self.max_feed.get('pig', {}).get(ft, 50.0)
            return m.pig_feed_winter[y, ft] <= limit

        m.max_pig_winter = Constraint(m.Y, m.FEED, rule=max_pig_winter_rule)

        def milk_summer_rule(m: Model, y):
            """Летний удой = базовый + прибавка от дополнительного кормления (убывающая отдача)"""

            gain = sum(
                self.feed_efficiency.get('milk', {}).get(ft, 0) *
                (1 - exp(-self.diminishing_beta.get('milk', 0.12) * m.extra_cow_summer[y, ft]))
                for ft in m.FEED
            )
            return m.milk_yield_summer[y] == self.base_milk_yield + gain * 30

        m.milk_summer_rule = Constraint(m.Y, rule=milk_summer_rule)

        def milk_winter_rule(m: Model, y):
            """Зимний удой = (базовый + прибавка) × зимний коэффициент снижения (0.82)"""

            gain = sum(
                self.feed_efficiency.get('milk', {}).get(ft, 0) *
                (1 - exp(-self.diminishing_beta.get('milk', 0.12) * m.extra_cow_winter[y, ft]))
                for ft in m.FEED
            )
            return m.milk_yield_winter[y] == (self.base_milk_yield + gain * 20) * self.winter_productivity_factor.get(
                'milk', 0.82)

        m.milk_winter_rule = Constraint(m.Y, rule=milk_winter_rule)

        def feed_balance_rule(m: Model, y, ft):
            """
            Баланс кормов по типам:
            Произведённые корма * 1000 ≥ (суточное потребление за год)
            """

            summer_demand = (m.cow_feed_summer[y, ft] * m.cows[y] + #type: ignore
                             m.cattle_feed_summer[y, ft] * m.cattle[y] + #type: ignore
                             m.pig_feed_summer[y, ft] * m.pigs[y]) #type: ignore
            winter_demand = (m.cow_feed_winter[y, ft] * m.cows[y] + #type: ignore
                             m.cattle_feed_winter[y, ft] * m.cattle[y] + #type: ignore
                             m.pig_feed_winter[y, ft] * m.pigs[y]) #type: ignore
            total_demand = (summer_demand * self.summer_days + winter_demand * self.winter_days) / 365
            return m.feed_prod[y, ft] * 1000 >= total_demand / 100 #type: ignore

        m.feed_balance = Constraint(m.Y, m.FEED, rule=feed_balance_rule)

        def crop_rotation_rule(m: Model, c, f):
            """Запрет на повторный посев одной культуры на том же поле"""

            if c in ['grass', 'fallow']:
                return pyo.Constraint.Skip

            return m.area[c, f, 1] + m.area[c, f, 2] <= self.field_area[f] * 0.5

        m.crop_rotation_constraint = Constraint(m.C, m.F, rule=crop_rotation_rule)

        def potato_rotation_rule(m: Model, f):
            """Картофель нельзя сажать на том же поле два года подряд"""

            return m.area['potato', f, 1] + m.area['potato', f, 2] <= self.field_area[f] * 0.6

        m.potato_rotation = Constraint(m.F, rule=potato_rotation_rule)

        def objective_rule(m: Model):
            """
            Целевая функция: максимизация чистой прибыли

            Доходы:
            - Выручка от продажи культур
            - Выручка от молока
            - Выручка от мяса (говядина, свинина)

            Расходы:
            - Затраты на выращивание культур
            - Затраты на удобрения
            - Затраты на корма (летом и зимой)
            - Затраты на содержание животных
            - Зимние энергозатраты
            """

            total_profit = 0

            for year in m.Y:
                year_val = pyo.value(year)

                crop_revenue_year = sum(
                    self.price.get(c, 0) * m.production[c, f, year]
                    for c in m.C for f in m.F
                )

                crop_costs_year = sum(
                    self.cost.get(c, 0) * m.area[c, f, year]
                    for c in m.C for f in m.F
                )

                fert_costs_year = sum(
                    self.fert_cost * m.fert[f, year] * self.field_area.get(f, 0)
                    for f in m.F
                )

                milk_revenue_year = (
                                            self.milk_price * m.milk_yield_summer[year] * m.cows[
                                        year] * self.summer_days +
                                            self.milk_price * m.milk_yield_winter[year] * m.cows[
                                                year] * self.winter_days
                                    ) / 365

                feed_costs_year = 0
                for ft in m.FEED:
                    feed_costs_year += self.feed_price_summer.get(ft, 0) * (
                            m.cow_feed_summer[year, ft] * m.cows[year] +
                            m.cattle_feed_summer[year, ft] * m.cattle[year] +
                            m.pig_feed_summer[year, ft] * m.pigs[year]
                    ) * self.summer_days
                    feed_costs_year += self.feed_price_winter.get(ft, 0) * (
                            m.cow_feed_winter[year, ft] * m.cows[year] +
                            m.cattle_feed_winter[year, ft] * m.cattle[year] +
                            m.pig_feed_winter[year, ft] * m.pigs[year]
                    ) * self.winter_days
                feed_costs_year = feed_costs_year / 365 / 100

                cow_costs_year = (
                                             self.cow_cost_summer * self.summer_days + self.cow_cost_winter * self.winter_days) / 365 * \
                                 m.cows[year]
                cattle_costs_year = (
                                                self.cattle_cost_summer * self.summer_days + self.cattle_cost_winter * self.winter_days) / 365 * \
                                    m.cattle[year]
                pig_costs_year = (
                                             self.pig_cost_summer * self.summer_days + self.pig_cost_winter * self.winter_days) / 365 * \
                                 m.pigs[year]

                winter_energy_year = (
                                             self.energy_cost_cow_winter * m.cows[year] +
                                             self.energy_cost_cattle_winter * m.cattle[year] +
                                             self.energy_cost_pig_winter * m.pigs[year]
                                     ) * (self.winter_days / 365)

                animal_costs_year = cow_costs_year + cattle_costs_year + pig_costs_year + winter_energy_year + feed_costs_year

                beef_revenue_year = self.beef_price * self.base_beef_yield * m.cattle[year] * 0.9
                pork_revenue_year = self.pork_price * self.base_pork_yield * m.pigs[year] * 0.95

                year_profit = (crop_revenue_year - crop_costs_year - fert_costs_year +
                               milk_revenue_year + beef_revenue_year + pork_revenue_year - animal_costs_year)

                total_profit += year_profit

            return total_profit * self.seasonal_adjustment

        m.obj = Objective(rule=objective_rule, sense=maximize)

    def get_solver(self):
        solver = pyo.SolverFactory('ipopt')
        return solver

    def solve(self) -> bool:
        self.build_model()
        solver = self.get_solver()
        logger.info("IPOPT start (нелинейная оптимизация)")
        results = solver.solve(self.model, tee=True)

        if (results.solver.status == SolverStatus.ok and
                results.solver.termination_condition == TerminationCondition.optimal):
            logger.info("\nОптимальное решение найдено")
            obj_val = value(self.model.obj)
            logger.info(f"Прибыль: {obj_val:,.0f} BYN")
            return True

        else:
            logger.error(f"Статус: {results.solver.termination_condition}")
            raise

    def print_results(self) -> None:
        """Вывод результатов с графиками и прибылью по годам"""

        import matplotlib.pyplot as plt
        import numpy as np

        m = self.model

        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.facecolor'] = '#1e1e1e'
        plt.rcParams['axes.facecolor'] = '#2d2d2d'

        print("\n" + "=" * 80)
        print("🌾 ОПТИМИЗАЦИЯ СЕЛЬСКОГО ХОЗЯЙСТВА БЕЛАРУСИ")
        print("=" * 80)

        years_data = {}
        all_crops = set()

        for y in m.Y:
            year_val = int(pyo.value(y))
            weather_data = self.weather[year_val]

            # Погода
            if isinstance(weather_data, dict) and 'temp' in weather_data and 'rain' in weather_data:
                avg_temp = weather_data['temp']
                total_rain = weather_data['rain']
                weather_desc = weather_data.get('desc', f'Год {year_val}')
            else:
                temps = [weather_data[m]['temp'] for m in range(1, 13) if m in weather_data]
                rains = [weather_data[m]['rain'] for m in range(1, 13) if m in weather_data]
                avg_temp = sum(temps) / len(temps) if temps else 0
                total_rain = sum(rains) if rains else 0
                weather_desc = f'Год {year_val}'

            # Животноводство
            years_data[year_val] = {
                'cows': pyo.value(m.cows[y]),
                'cattle': pyo.value(m.cattle[y]),
                'pigs': pyo.value(m.pigs[y]),
                'milk_summer': pyo.value(m.milk_yield_summer[y]) or 0,
                'milk_winter': pyo.value(m.milk_yield_winter[y]) or 0,
                'crops': {},
                'avg_temp': avg_temp,
                'total_rain': total_rain
            }

            # Посевы
            for f in m.F:
                for c in m.C:
                    area = pyo.value(m.area[c, f, y])
                    if area > 0.5:
                        years_data[year_val]['crops'][c] = years_data[year_val]['crops'].get(c, 0) + area
                        if c != 'fallow':
                            all_crops.add(c)

        years = sorted(years_data.keys())

        # ========== ТЕКСТОВЫЙ ВЫВОД ==========
        for year_val, data in years_data.items():
            print(f"\n{'─' * 80}")
            print(f"📅 ГОД {year_val}")
            print(f"🌡️  {data['avg_temp']:.1f}°C | 💧 {data['total_rain']:.0f} мм")
            print(f"{'─' * 80}")

            print(f"\n🐄 ЖИВОТНОВОДСТВО:")
            print(
                f"   Коровы: {data['cows']:>8.0f} гол. | КРС: {data['cattle']:>8.0f} гол. | Свиньи: {data['pigs']:>8.0f} гол.")
            print(f"   Удой лето: {data['milk_summer']:>8.0f} кг/гол | зима: {data['milk_winter']:>8.0f} кг/гол")

            print(f"\n🌾 ПОСЕВЫ (га):")
            for crop, area in sorted(data['crops'].items(), key=lambda x: -x[1]):
                if crop != 'fallow':
                    print(f"   {crop:20} : {area:>8.1f} га ({area / self.total_land * 100:>5.1f}%)")

            fallow = data['crops'].get('fallow', 0)
            if fallow > 0:
                print(f"   {'пар':20} : {fallow:>8.1f} га ({fallow / self.total_land * 100:>5.1f}%)")

        # ========== РАСЧЁТ ПРИБЫЛИ ==========
        profits = {}
        crop_names_ru = {
            'winter_wheat': 'Озимая пшеница', 'spring_wheat': 'Яровая пшеница',
            'barley': 'Ячмень', 'rapeseed': 'Рапс', 'potato': 'Картофель',
            'sugar_beet': 'Сахарная свёкла', 'corn_silage': 'Кукуруза силос', 'grass': 'Травы'
        }

        for year_val, data in years_data.items():
            # Доходы и затраты
            crop_revenue = sum(self.price.get(c, 0) * pyo.value(m.production[c, f, year_val]) for c in m.C for f in m.F)
            crop_costs = sum(self.cost.get(c, 0) * pyo.value(m.area[c, f, year_val]) for c in m.C for f in m.F)
            fert_costs = sum(self.fert_cost * pyo.value(m.fert[f, year_val]) * self.field_area.get(f, 0) for f in m.F)

            milk_revenue = (self.milk_price * data['milk_summer'] * data['cows'] * self.summer_days +
                            self.milk_price * data['milk_winter'] * data['cows'] * self.winter_days) / 365

            # Затраты на корма
            feed_costs = 0
            for ft in m.FEED:
                feed_costs += self.feed_price_summer.get(ft, 0) * (
                        pyo.value(m.cow_feed_summer[year_val, ft]) * data['cows'] +
                        pyo.value(m.cattle_feed_summer[year_val, ft]) * data['cattle'] +
                        pyo.value(m.pig_feed_summer[year_val, ft]) * data['pigs']
                ) * self.summer_days
                feed_costs += self.feed_price_winter.get(ft, 0) * (
                        pyo.value(m.cow_feed_winter[year_val, ft]) * data['cows'] +
                        pyo.value(m.cattle_feed_winter[year_val, ft]) * data['cattle'] +
                        pyo.value(m.pig_feed_winter[year_val, ft]) * data['pigs']
                ) * self.winter_days
            feed_costs = feed_costs / 365 / 100

            # Затраты на животных
            cow_costs = (self.cow_cost_summer * self.summer_days + self.cow_cost_winter * self.winter_days) / 365 * \
                        data['cows']
            cattle_costs = (
                                       self.cattle_cost_summer * self.summer_days + self.cattle_cost_winter * self.winter_days) / 365 * \
                           data['cattle']
            pig_costs = (self.pig_cost_summer * self.summer_days + self.pig_cost_winter * self.winter_days) / 365 * \
                        data['pigs']

            winter_energy = (self.energy_cost_cow_winter * data['cows'] +
                             self.energy_cost_cattle_winter * data['cattle'] +
                             self.energy_cost_pig_winter * data['pigs']) * (self.winter_days / 365)

            animal_costs = cow_costs + cattle_costs + pig_costs + winter_energy + feed_costs

            beef_revenue = self.beef_price * self.base_beef_yield * data['cattle'] * 0.9
            pork_revenue = self.pork_price * self.base_pork_yield * data['pigs'] * 0.95

            profits[
                year_val] = crop_revenue - crop_costs - fert_costs + milk_revenue + beef_revenue + pork_revenue - animal_costs

        # ========== ГРАФИКИ ==========
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Структура посевов и прибыль по годам', fontsize=14, fontweight='bold', color='white')

        # Круговые диаграммы
        for i, year in enumerate(years):
            crops_list = [c for c in years_data[year]['crops'].keys() if c != 'fallow']
            if crops_list:
                areas = [years_data[year]['crops'].get(c, 0) for c in crops_list]
                labels = [crop_names_ru.get(c, c) for c in crops_list]
                colors = plt.cm.Set3(np.linspace(0, 1, len(crops_list)))
                axes[0, i].pie(areas, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                axes[0, i].set_title(f'Структура посевов (Год {year})', fontsize=12, color='white')
            else:
                axes[0, i].text(0.5, 0.5, 'Нет данных', ha='center', va='center', color='white')
                axes[0, i].set_title(f'Структура посевов (Год {year})', fontsize=12, color='white')

        # Сравнение площадей
        all_crops_list = sorted([c for c in all_crops if c != 'fallow'])
        if all_crops_list:
            x = np.arange(len(all_crops_list))
            width = 0.35
            areas1 = [years_data[years[0]]['crops'].get(c, 0) for c in all_crops_list]
            areas2 = [years_data[years[1]]['crops'].get(c, 0) for c in all_crops_list]
            labels = [crop_names_ru.get(c, c) for c in all_crops_list]

            axes[1, 0].bar(x - width / 2, areas1, width, label=f'Год {years[0]}', color='#66c2a5')
            axes[1, 0].bar(x + width / 2, areas2, width, label=f'Год {years[1]}', color='#fc8d62')
            axes[1, 0].set_ylabel('Площадь (га)', color='white')
            axes[1, 0].set_title('Сравнение посевных площадей', fontsize=12, color='white')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(labels, rotation=45, ha='right', color='white')
            axes[1, 0].legend()
            axes[1, 0].tick_params(axis='y', colors='white')
            axes[1, 0].grid(axis='y', alpha=0.3, color='gray')
        else:
            axes[1, 0].text(0.5, 0.5, 'Нет данных', ha='center', va='center', color='white')
            axes[1, 0].set_title('Сравнение посевных площадей', fontsize=12, color='white')

        # График прибыли
        profits_list = [profits[y] for y in years]
        bars = axes[1, 1].bar(years, profits_list, color=['#66c2a5', '#fc8d62'])
        axes[1, 1].set_ylabel('Прибыль (BYN)', color='white')
        axes[1, 1].set_title('Прибыль по годам', fontsize=12, color='white')
        axes[1, 1].tick_params(axis='y', colors='white')
        axes[1, 1].tick_params(axis='x', colors='white')
        axes[1, 1].grid(axis='y', alpha=0.3, color='gray')

        for bar, profit in zip(bars, profits_list):
            axes[1, 1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50000,
                            f'{profit:,.0f}', ha='center', va='bottom', fontsize=10, color='white')

        plt.tight_layout()
        plt.show()

        # ========== ИТОГ ==========
        total = pyo.value(m.obj)
        print(f"\n{'=' * 80}")
        print(f"🏆 ОБЩАЯ ПРИБЫЛЬ ЗА 2 ГОДА: {total:>15,.0f} BYN")
        print(f"💰 СРЕДНЕГОДОВАЯ ПРИБЫЛЬ: {total / 2:>15,.0f} BYN")
        print(f"\n📊 ПРИБЫЛЬ ПО ГОДАМ:")
        print(f"   Год {years[0]}: {profits[years[0]]:>15,.0f} BYN")
        print(f"   Год {years[1]}: {profits[years[1]]:>15,.0f} BYN")
        print("=" * 80)
