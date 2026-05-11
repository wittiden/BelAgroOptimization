# app/models_with_repo.py

import pyomo.environ as pyo
from pyomo.environ import value, exp, Constraint, Objective, maximize, Var
from pyomo.opt import SolverStatus, TerminationCondition


class BelarusAgroModel:
    """Оптимизационная модель с загрузкой данных из репозитория"""

    def __init__(self, data: dict):
        self.model = pyo.ConcreteModel()
        self.data = data
        self._load_data_to_model()

    def _load_data_to_model(self):
        """Загрузка данных из словаря в атрибуты модели"""
        for key, value in self.data.items():
            setattr(self, key, value)

    def get_weather_factor(self, crop: str, year: int) -> float:
        """Расчёт погодного коэффициента"""
        rain = self.weather[year]['rain']
        temp = self.weather[year]['temp']

        sensitivity = {
            'winter_wheat': 0.30, 'spring_wheat': 0.35, 'barley': 0.30,
            'rapeseed': 0.45, 'potato': 0.50, 'sugar_beet': 0.40,
            'corn_silage': 0.42, 'grass': 0.38, 'fallow': 0
        }

        if rain >= 550:
            rain_factor = 1.0
        else:
            drought = (550 - rain) / 550
            rain_factor = 1 - drought * sensitivity.get(crop, 0.40)
            rain_factor = max(0.65, rain_factor)

        if crop.startswith('winter'):
            temp_factor = 1.0 if temp <= 22 else 1 - 0.05 * (temp - 22)
        else:
            temp_factor = 1.0 if temp <= 20 else 1 - 0.06 * (temp - 20)

        temp_factor = max(0.7, temp_factor)

        return rain_factor * temp_factor

    def build_model(self):
        """Построение модели Pyomo"""
        m = self.model

        # Множества
        m.C = pyo.Set(initialize=self.crops)
        m.F = pyo.Set(initialize=self.fields)
        m.Y = pyo.Set(initialize=self.years)
        m.FEED = pyo.Set(initialize=self.feed_types)

        # Переменные
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

        # ========== ОГРАНИЧЕНИЯ ==========

        def land_rule(m, f, y):
            return sum(m.area[c, f, y] for c in m.C) <= self.field_area[f]

        m.land_limit = Constraint(m.F, m.Y, rule=land_rule)

        def grain_rule(m, y):
            grain = sum(
                m.area['winter_wheat', f, y] + m.area['spring_wheat', f, y] + m.area['barley', f, y] for f in m.F)
            return grain >= self.total_land * self.grain_min_pct

        m.grain_rule = Constraint(m.Y, rule=grain_rule)

        def feed_crop_rule(m, y):
            feed_area = sum(m.area['corn_silage', f, y] + m.area['grass', f, y] for f in m.F)
            return feed_area >= self.total_land * self.feed_crop_min_pct

        m.feed_crop_rule = Constraint(m.Y, rule=feed_crop_rule)

        def fallow_rule(m, y):
            fallow_area = sum(m.area['fallow', f, y] for f in m.F)
            return fallow_area >= self.total_land * self.fallow_min_pct

        m.fallow_rule = Constraint(m.Y, rule=fallow_rule)

        def potato_rule(m, y):
            return sum(m.area['potato', f, y] for f in m.F) <= self.total_land * self.potato_max_pct

        m.potato_rule = Constraint(m.Y, rule=potato_rule)

        def rape_rule(m, y):
            return sum(m.area['rapeseed', f, y] for f in m.F) <= self.total_land * self.rapeseed_max_pct

        m.rape_rule = Constraint(m.Y, rule=rape_rule)

        def prod_rule(m, c, f, y):
            wf = self.get_weather_factor(c, y)
            fert_effect = (self.fert_response[c] * m.fert[f, y]) / (1 + 0.015 * m.fert[f, y])
            yield_per_ha = (self.base_yield[c] + fert_effect) * wf
            return m.production[c, f, y] == yield_per_ha * m.area[c, f, y]

        m.prod_rule = Constraint(m.C, m.F, m.Y, rule=prod_rule)

        def feed_prod_rule(m, y, ft):
            return m.feed_prod[y, ft] == sum(
                m.production[c, f, y] * self.feed_output.get(c, {}).get(ft, 0)
                for c in m.C for f in m.F
            )

        m.feed_prod_rule = Constraint(m.Y, m.FEED, rule=feed_prod_rule)

        # Extra кормление
        def extra_cow_summer_rule(m, y, ft):
            return m.extra_cow_summer[y, ft] >= m.cow_feed_summer[y, ft] - self.base_feed_need_summer['cow'][ft]

        m.extra_cow_summer_rule = Constraint(m.Y, m.FEED, rule=extra_cow_summer_rule)

        def extra_cow_winter_rule(m, y, ft):
            return m.extra_cow_winter[y, ft] >= m.cow_feed_winter[y, ft] - self.base_feed_need_winter['cow'][ft]

        m.extra_cow_winter_rule = Constraint(m.Y, m.FEED, rule=extra_cow_winter_rule)

        def extra_cattle_summer_rule(m, y, ft):
            return m.extra_cattle_summer[y, ft] >= m.cattle_feed_summer[y, ft] - self.base_feed_need_summer['cattle'][
                ft]

        m.extra_cattle_summer_rule = Constraint(m.Y, m.FEED, rule=extra_cattle_summer_rule)

        def extra_cattle_winter_rule(m, y, ft):
            return m.extra_cattle_winter[y, ft] >= m.cattle_feed_winter[y, ft] - self.base_feed_need_winter['cattle'][
                ft]

        m.extra_cattle_winter_rule = Constraint(m.Y, m.FEED, rule=extra_cattle_winter_rule)

        def extra_pig_summer_rule(m, y, ft):
            return m.extra_pig_summer[y, ft] >= m.pig_feed_summer[y, ft] - self.base_feed_need_summer['pig'][ft]

        m.extra_pig_summer_rule = Constraint(m.Y, m.FEED, rule=extra_pig_summer_rule)

        def extra_pig_winter_rule(m, y, ft):
            return m.extra_pig_winter[y, ft] >= m.pig_feed_winter[y, ft] - self.base_feed_need_winter['pig'][ft]

        m.extra_pig_winter_rule = Constraint(m.Y, m.FEED, rule=extra_pig_winter_rule)

        # Минимальное кормление
        def min_cow_summer_rule(m, y, ft):
            return m.cow_feed_summer[y, ft] >= self.base_feed_need_summer['cow'][ft]

        m.min_cow_summer = Constraint(m.Y, m.FEED, rule=min_cow_summer_rule)

        def min_cow_winter_rule(m, y, ft):
            return m.cow_feed_winter[y, ft] >= self.base_feed_need_winter['cow'][ft]

        m.min_cow_winter = Constraint(m.Y, m.FEED, rule=min_cow_winter_rule)

        def min_cattle_summer_rule(m, y, ft):
            return m.cattle_feed_summer[y, ft] >= self.base_feed_need_summer['cattle'][ft]

        m.min_cattle_summer = Constraint(m.Y, m.FEED, rule=min_cattle_summer_rule)

        def min_cattle_winter_rule(m, y, ft):
            return m.cattle_feed_winter[y, ft] >= self.base_feed_need_winter['cattle'][ft]

        m.min_cattle_winter = Constraint(m.Y, m.FEED, rule=min_cattle_winter_rule)

        def min_pig_summer_rule(m, y, ft):
            return m.pig_feed_summer[y, ft] >= self.base_feed_need_summer['pig'][ft]

        m.min_pig_summer = Constraint(m.Y, m.FEED, rule=min_pig_summer_rule)

        def min_pig_winter_rule(m, y, ft):
            return m.pig_feed_winter[y, ft] >= self.base_feed_need_winter['pig'][ft]

        m.min_pig_winter = Constraint(m.Y, m.FEED, rule=min_pig_winter_rule)

        # Максимальное кормление
        def max_cow_summer_rule(m, y, ft):
            return m.cow_feed_summer[y, ft] <= self.max_feed['cow'][ft]

        m.max_cow_summer = Constraint(m.Y, m.FEED, rule=max_cow_summer_rule)

        def max_cow_winter_rule(m, y, ft):
            return m.cow_feed_winter[y, ft] <= self.max_feed['cow'][ft]

        m.max_cow_winter = Constraint(m.Y, m.FEED, rule=max_cow_winter_rule)

        def max_cattle_summer_rule(m, y, ft):
            return m.cattle_feed_summer[y, ft] <= self.max_feed['cattle'][ft]

        m.max_cattle_summer = Constraint(m.Y, m.FEED, rule=max_cattle_summer_rule)

        def max_cattle_winter_rule(m, y, ft):
            return m.cattle_feed_winter[y, ft] <= self.max_feed['cattle'][ft]

        m.max_cattle_winter = Constraint(m.Y, m.FEED, rule=max_cattle_winter_rule)

        def max_pig_summer_rule(m, y, ft):
            return m.pig_feed_summer[y, ft] <= self.max_feed['pig'][ft]

        m.max_pig_summer = Constraint(m.Y, m.FEED, rule=max_pig_summer_rule)

        def max_pig_winter_rule(m, y, ft):
            return m.pig_feed_winter[y, ft] <= self.max_feed['pig'][ft]

        m.max_pig_winter = Constraint(m.Y, m.FEED, rule=max_pig_winter_rule)

        # Продуктивность
        def milk_summer_rule(m, y):
            gain = sum(
                self.feed_efficiency['milk'][ft] * (1 - exp(-self.diminishing_beta['milk'] * m.extra_cow_summer[y, ft]))
                for ft in m.FEED)
            return m.milk_yield_summer[y] == self.base_milk_yield + gain * 30

        m.milk_summer_rule = Constraint(m.Y, rule=milk_summer_rule)

        def milk_winter_rule(m, y):
            gain = sum(
                self.feed_efficiency['milk'][ft] * (1 - exp(-self.diminishing_beta['milk'] * m.extra_cow_winter[y, ft]))
                for ft in m.FEED)
            return m.milk_yield_winter[y] == (self.base_milk_yield + gain * 20) * self.winter_productivity_factor[
                'milk']

        m.milk_winter_rule = Constraint(m.Y, rule=milk_winter_rule)

        # Баланс кормов
        def feed_balance_rule(m, y, ft):
            summer_demand = (m.cow_feed_summer[y, ft] * m.cows[y] +
                             m.cattle_feed_summer[y, ft] * m.cattle[y] +
                             m.pig_feed_summer[y, ft] * m.pigs[y])
            winter_demand = (m.cow_feed_winter[y, ft] * m.cows[y] +
                             m.cattle_feed_winter[y, ft] * m.cattle[y] +
                             m.pig_feed_winter[y, ft] * m.pigs[y])
            total_demand = (summer_demand * self.summer_days + winter_demand * self.winter_days) / 365
            return m.feed_prod[y, ft] * 1000 >= total_demand / 100

        m.feed_balance = Constraint(m.Y, m.FEED, rule=feed_balance_rule)

        # ========== ЦЕЛЕВАЯ ФУНКЦИЯ ==========

        def objective_rule(m):
            crop_revenue = sum(self.price[c] * m.production[c, f, y] for c in m.C for f in m.F for y in m.Y)
            crop_costs = sum(self.cost[c] * m.area[c, f, y] for c in m.C for f in m.F for y in m.Y)
            fert_costs = sum(self.fert_cost * m.fert[f, y] * self.field_area[f] for f in m.F for y in m.Y)

            milk_revenue = 0
            for y in m.Y:
                milk_summer_rev = self.milk_price * m.milk_yield_summer[y] * m.cows[y] * self.summer_days
                milk_winter_rev = self.milk_price * m.milk_yield_winter[y] * m.cows[y] * self.winter_days
                milk_revenue += (milk_summer_rev + milk_winter_rev) / 365

            feed_costs_summer = 0
            feed_costs_winter = 0
            for y in m.Y:
                for ft in m.FEED:
                    feed_costs_summer += self.feed_price_summer[ft] * (
                            m.cow_feed_summer[y, ft] * m.cows[y] +
                            m.cattle_feed_summer[y, ft] * m.cattle[y] +
                            m.pig_feed_summer[y, ft] * m.pigs[y]
                    ) * self.summer_days
                    feed_costs_winter += self.feed_price_winter[ft] * (
                            m.cow_feed_winter[y, ft] * m.cows[y] +
                            m.cattle_feed_winter[y, ft] * m.cattle[y] +
                            m.pig_feed_winter[y, ft] * m.pigs[y]
                    ) * self.winter_days
            feed_costs = (feed_costs_summer + feed_costs_winter) / 365 / 100

            cow_costs = 0
            cattle_costs = 0
            pig_costs = 0
            for y in m.Y:
                cow_costs += (self.cow_cost_summer * self.summer_days + self.cow_cost_winter * self.winter_days) / 365 * \
                             m.cows[y]
                cattle_costs += (
                                            self.cattle_cost_summer * self.summer_days + self.cattle_cost_winter * self.winter_days) / 365 * \
                                m.cattle[y]
                pig_costs += (self.pig_cost_summer * self.summer_days + self.pig_cost_winter * self.winter_days) / 365 * \
                             m.pigs[y]

            winter_energy = 0
            for y in m.Y:
                winter_energy += (self.energy_cost_cow_winter * m.cows[y] +
                                  self.energy_cost_cattle_winter * m.cattle[y] +
                                  self.energy_cost_pig_winter * m.pigs[y]) * (self.winter_days / 365)

            animal_costs = cow_costs + cattle_costs + pig_costs + winter_energy + feed_costs

            beef_revenue = 0
            pork_revenue = 0
            for y in m.Y:
                beef_revenue += self.beef_price * self.base_beef_yield * m.cattle[y] * 0.9
                pork_revenue += self.pork_price * self.base_pork_yield * m.pigs[y] * 0.95

            total = (crop_revenue - crop_costs - fert_costs +
                     milk_revenue + beef_revenue + pork_revenue - animal_costs)

            return total * self.seasonal_adjustment

        m.obj = Objective(rule=objective_rule, sense=maximize)

    def get_solver(self):
        solver = pyo.SolverFactory('ipopt')
        solver.options['tol'] = 1e-6
        solver.options['max_iter'] = 5000
        solver.options['print_level'] = 5
        solver.options['mu_strategy'] = 'adaptive'
        return solver

    def solve(self):
        self.build_model()
        solver = self.get_solver()
        print("✅ Используем IPOPT (нелинейная оптимизация)")
        results = solver.solve(self.model, tee=True)

        if (results.solver.status == SolverStatus.ok and
                results.solver.termination_condition == TerminationCondition.optimal):
            print("\n✅ Оптимальное решение найдено")
            obj_val = value(self.model.obj)
            print(f"💰 Прибыль: {obj_val:,.0f} BYN")
            return True
        else:
            print(f"⚠️ Статус: {results.solver.termination_condition}")
            return False

    def print_results(self):
        m = self.model

        print("\n" + "=" * 80)
        print("ОПТИМИЗАЦИЯ СЕЛЬСКОГО ХОЗЯЙСТВА БЕЛАРУСИ")
        print("=" * 80)

        for y in m.Y:
            year_val = value(y)
            print(f"\nГОД {year_val}: {self.weather[year_val]['desc']}")
            print("-" * 50)

            cows = value(m.cows[y])
            cattle = value(m.cattle[y])
            pigs = value(m.pigs[y])

            print(f"\nЖИВОТНОВОДСТВО:")
            print(f"   Коровы: {cows:.0f} гол.")
            print(f"   КРС: {cattle:.0f} гол.")
            print(f"   Свиньи: {pigs:.0f} гол.")

            milk_summer = value(m.milk_yield_summer[y]) or 0
            milk_winter = value(m.milk_yield_winter[y]) or 0
            print(f"   Удой летом: {milk_summer:.0f} кг/гол")
            print(f"   Удой зимой: {milk_winter:.0f} кг/гол")

            print(f"\nПОСЕВЫ:")
            for f in m.F:
                for c in m.C:
                    area = value(m.area[c, f, y])
                    if area > 1 and c != 'fallow':
                        prod = value(m.production[c, f, y]) or 0
                        print(f"   {f} | {c} | {area:.1f} га | {prod:.0f} ц")

        total = value(m.obj)
        print(f"\nИТОГОВАЯ ПРИБЫЛЬ: {total:,.0f} BYN")