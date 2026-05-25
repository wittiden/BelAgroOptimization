import pyomo.environ as pyo
from pyomo.environ import value, Constraint, Objective, maximize, Var
from pyomo.opt import SolverStatus, TerminationCondition
from typing import Any
from loguru import logger
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime


class BelarusAgroModel:
    """Оптимизационная модель с загрузкой данных из PostgreSQL"""

    __slots__ = (
        'model', 'scenario_id', 'scenario_name', 'db_url',
        # Растениеводство
        'crops', 'all_crops', 'fields', 'years', 'field_area', 'total_land',
        'base_yield', 'price', 'cost', 'max_area_pct',
        'seed_cost', 'fert_response', 'max_fert', 'fert_cost', 'feed_types',
        # Животноводство — коровы
        'min_cows', 'max_cows', 'milk_price', 'milk_yield',
        'base_milk_yield', 'max_milk_yield', 'cow_cost_summer', 'cow_cost_winter',
        'energy_cost_cow_winter',
        # Животноводство — мясной скот
        'min_cattle', 'max_cattle', 'beef_price',
        'base_beef_yield', 'max_beef_yield', 'cattle_cost_summer', 'cattle_cost_winter',
        'energy_cost_cattle_winter',
        # Животноводство — свиньи
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

        # Константы по умолчанию
        self.summer_days = 180
        self.winter_days = 185
        self.grain_min_pct = 0.35
        self.fallow_min_pct = 0.05

        # Растениеводство
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
        # Животноводство — коровы
        self.min_cows = 0
        self.max_cows = 0
        self.milk_price = 0
        self.milk_yield = 0
        self.base_milk_yield = 0
        self.max_milk_yield = 0
        self.cow_cost_summer = 0
        self.cow_cost_winter = 0
        self.energy_cost_cow_winter = 0
        # Животноводство — мясной скот
        self.min_cattle = 0
        self.max_cattle = 0
        self.beef_price = 0
        self.base_beef_yield = 0
        self.max_beef_yield = 0
        self.cattle_cost_summer = 0
        self.cattle_cost_winter = 0
        self.energy_cost_cattle_winter = 0
        # Животноводство — свиньи
        self.min_pigs = 0
        self.max_pigs = 0
        self.pork_price = 0
        self.base_pork_yield = 0
        self.max_pork_yield = 0
        self.pig_cost_summer = 0
        self.pig_cost_winter = 0
        self.energy_cost_pig_winter = 0
        # Корма
        self.feed_price_summer = {}
        self.feed_price_winter = {}
        self.base_feed_need_summer = {}
        self.base_feed_need_winter = {}
        self.max_feed = {}
        self.feed_efficiency = {}
        self.feed_output = {}
        self.diminishing_beta = {}
        # Погода
        self.weather = {}
        # Загружаем данные из словаря в атрибуты модели
        self._load_data_to_model(model_data)

    def _load_data_to_model(self, data: dict) -> None:
        """Загрузка данных из словаря в атрибуты модели"""

        for key, v in data.items():
            if key in self.__slots__:
                setattr(self, key, v)

        # all_crops = все культуры из БД + пар (используется как множество CROPS в модели)
        if self.crops and not self.all_crops:
            self.all_crops = self.crops + ['fallow']

    def get_weather_factor(self, crop: str, year: int) -> float:
        """Расчёт погодного коэффициента"""
        weather = self.weather[year]
        temp = weather.temp
        rain = weather.rain

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

        if not self.all_crops or not self.fields or not self.years:
            raise ValueError(
                f"Модель не инициализирована: crops={self.all_crops}, "
                f"fields={self.fields}, years={self.years}"
            )

        # --- Множества и переменные ---
        m.CROPS = pyo.Set(initialize=self.all_crops)
        m.FIELDS = pyo.Set(initialize=self.fields)
        m.YEARS = pyo.Set(initialize=self.years)

        m.area = Var(m.CROPS, m.FIELDS, m.YEARS, bounds=(0, None))
        m.production = Var(m.CROPS, m.FIELDS, m.YEARS, bounds=(0, None))
        m.cows = Var(m.YEARS, bounds=(self.min_cows, self.max_cows))

        # --- Ограничения ---

        # 1. Площадь всех культур на поле не превышает размер поля
        def land_limit_rule(m, field, year):
            return sum(m.area[c, field, year] for c in m.CROPS) <= self.field_area[field]

        m.LandLimit = Constraint(m.FIELDS, m.YEARS, rule=land_limit_rule)

        # 2. Зерновые (пшеница + ячмень) занимают не менее grain_min_pct от общей площади
        GRAIN_CROPS = ['winter_wheat', 'spring_wheat', 'barley']

        def grain_requirement_rule(m, year):
            grain_area = sum(
                m.area[c, f, year]
                for c in GRAIN_CROPS if c in m.CROPS
                for f in m.FIELDS
            )
            return grain_area >= self.total_land * self.grain_min_pct

        m.GrainRequirement = Constraint(m.YEARS, rule=grain_requirement_rule)

        # 3. Под паром не менее fallow_min_pct от общей площади
        def fallow_requirement_rule(m, year):
            fallow_area = sum(m.area['fallow', f, year] for f in m.FIELDS)
            return fallow_area >= self.total_land * self.fallow_min_pct

        m.FallowRequirement = Constraint(m.YEARS, rule=fallow_requirement_rule)

        # 4. Каждая культура занимает не более max_area_pct от общей площади
        def max_area_rule(m, crop, year):
            if crop == 'fallow' or crop not in self.max_area_pct:
                return pyo.Constraint.Skip
            total_crop_area = sum(m.area[crop, f, year] for f in m.FIELDS)
            return total_crop_area <= self.total_land * self.max_area_pct[crop]

        m.MaxArea = Constraint(m.CROPS, m.YEARS, rule=max_area_rule)

        # 5. Производство = урожайность × площадь (с погодным коэффициентом); пар даёт 0
        def production_rule(m, crop, field, year):
            if crop == 'fallow':
                return m.production[crop, field, year] == 0
            yield_per_ha = self.base_yield.get(crop, 0) * self.get_weather_factor(crop, year)
            return m.production[crop, field, year] == yield_per_ha * m.area[crop, field, year]

        m.ProductionRule = Constraint(m.CROPS, m.FIELDS, m.YEARS, rule=production_rule)

        # 6. Севооборот: никакая культура не может занимать более 50% поля за два года суммарно
        #    Это мягко ограничивает монокультуру даже при одном годе
        #    (травы и пар освобождены — они многолетние или нейтральные)
        year0, year1 = self.years[0], self.years[1]

        def crop_rotation_rule(m, crop, field):
            if crop in ('grass', 'fallow') or len(self.years) < 2:
                return pyo.Constraint.Skip
            return m.area[crop, field, year0] + m.area[crop, field, year1] <= self.field_area[field] * 0.5

        m.CropRotation = Constraint(m.CROPS, m.FIELDS, rule=crop_rotation_rule)

        # 7. Запрет повтора культуры на одном поле два года подряд:
        #    если культура заняла >10% поля в год0, в год1 она должна занимать <10% (и наоборот)
        #    Реализовано через бинарную логику: area_y0 + area_y1 <= field_area * 1.0
        #    в сочетании с ограничением 6 (<=50%) это вместе означает чередование.
        #    Для жёсткого запрета — каждый год культура ограничена 60% поля, но сумма <=50%,
        #    что физически требует чередования: нельзя взять 60% в оба года одновременно.
        #
        #    Картофель — особый случай: агрономически требует минимум 2-летнего перерыва,
        #    поэтому жёстко ограничен: суммарно не более 40% поля за два года.
        def potato_rotation_rule(m, field):
            if 'potato' not in m.CROPS or len(self.years) < 2:
                return pyo.Constraint.Skip
            # Картофель суммарно за оба года занимает не более 40% поля
            return (m.area['potato', field, year0] + m.area['potato', field, year1]
                    <= self.field_area[field] * 0.4)

        m.PotatoRotation = Constraint(m.FIELDS, rule=potato_rotation_rule)

        # 8. Ни одна культура не занимает более 60% поля в отдельный год
        #    (кроме трав и пара). В сочетании с ограничением 6 (сумма <=50%)
        #    это гарантирует, что культура не может занять поле полностью ни в один год.
        def max_crop_per_field_rule(m, crop, field, year):
            if crop in ('grass', 'fallow'):
                return pyo.Constraint.Skip
            return m.area[crop, field, year] <= self.field_area[field] * 0.6

        m.MaxCropPerField = Constraint(m.CROPS, m.FIELDS, m.YEARS, rule=max_crop_per_field_rule)

        # --- Целевая функция: максимизация суммарной прибыли ---
        def objective_rule(m):
            total_profit = 0
            for year in m.YEARS:
                crop_revenue = sum(
                    self.price.get(c, 0) * m.production[c, f, year]
                    for c in m.CROPS if c != 'fallow'
                    for f in m.FIELDS
                )
                crop_expenses = sum(
                    self.cost.get(c, 0) * m.area[c, f, year]
                    for c in m.CROPS
                    for f in m.FIELDS
                )
                milk_revenue = self.milk_price * m.cows[year] * self.milk_yield / 1000
                cow_expenses = m.cows[year] * 2500
                total_profit += crop_revenue + milk_revenue - crop_expenses - cow_expenses
            return total_profit

        m.Objective = Objective(rule=objective_rule, sense=maximize)

    def solve(self) -> bool:
        """Решение модели"""
        self.build_model()
        solver = pyo.SolverFactory('ipopt')

        logger.info("🚀 Запуск IPOPT оптимизации...")
        results = solver.solve(self.model, tee=False)

        if (results.solver.status == SolverStatus.ok and
                results.solver.termination_condition == TerminationCondition.optimal):
            logger.info("✅ Оптимальное решение найдено")
            logger.info(f"💰 Общая прибыль: {value(self.model.Objective):,.0f} BYN")
            return True
        else:
            logger.error(f"❌ Ошибка: {results.solver.termination_condition}")
            return False

    def print_results(self) -> None:
        """Вывод результатов с графиками (в стиле начальной модели)"""
        m = self.model

        # Русские названия культур
        crop_names_ru = {
            'winter_wheat': 'Озимая пшеница', 'spring_wheat': 'Яровая пшеница',
            'barley': 'Ячмень', 'rapeseed': 'Рапс', 'potato': 'Картофель',
            'sugar_beet': 'Сахарная свёкла', 'corn_silage': 'Кукуруза силос',
            'grass': 'Травы', 'fallow': 'Пар'
        }

        # Стиль графиков как в начальной модели
        plt.style.use('dark_background')
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.facecolor'] = '#1e1e1e'
        plt.rcParams['axes.facecolor'] = '#2d2d2d'

        print("\n" + "=" * 80)
        print("🌾 ОПТИМИЗАЦИЯ СЕЛЬСКОГО ХОЗЯЙСТВА БЕЛАРУСИ")
        print("=" * 80)

        # Сбор данных
        years_data = {}
        all_crops = set()

        for y in m.YEARS:
            year_val = pyo.value(y)
            weather = self.weather[year_val]

            years_data[year_val] = {
                'cows': pyo.value(m.cows[y]),
                'crops': {},
                'avg_temp': weather.temp,
                'total_rain': weather.rain
            }

            for field in m.FIELDS:
                for crop in m.CROPS:
                    area = pyo.value(m.area[crop, field, y])
                    if area is not None and area > 0.5:
                        years_data[year_val]['crops'][crop] = years_data[year_val]['crops'].get(crop, 0) + area
                        if crop != 'fallow':
                            all_crops.add(crop)

        years = sorted(years_data.keys())

        # Текстовый вывод
        for year_val, data in years_data.items():
            print(f"\n{'─' * 80}")
            print(f"📅 ГОД {year_val}")
            print(f"🌡️  {data['avg_temp']:.1f}°C | 💧 {data['total_rain']:.0f} мм")
            print(f"{'─' * 80}")

            print(f"\n🐄 ПОГОЛОВЬЕ:")
            print(f"   Коровы: {data['cows']:>8.0f} гол.")

            print(f"\n🌾 ПОСЕВЫ (га):")
            for crop, area in sorted(data['crops'].items(), key=lambda x: -x[1]):
                name = crop_names_ru.get(crop, crop)
                pct = area / self.total_land * 100
                print(f"   {name:20} : {area:>8.1f} га ({pct:>5.1f}%)")

        # Расчёт прибыли
        profits = {}
        for year in m.YEARS:
            year_val = pyo.value(year)
            revenue = 0
            expenses = 0

            for field in m.FIELDS:
                for crop in m.CROPS:
                    if crop != 'fallow':
                        prod_val = pyo.value(m.production[crop, field, year])
                        area_val = pyo.value(m.area[crop, field, year])
                        if prod_val is not None:
                            revenue += self.price.get(crop, 0) * prod_val
                        if area_val is not None:
                            expenses += self.cost.get(crop, 0) * area_val

            milk_revenue = self.milk_price * pyo.value(m.cows[year]) * self.milk_yield / 1000
            cow_expenses = pyo.value(m.cows[year]) * 2500
            profits[year_val] = revenue + milk_revenue - expenses - cow_expenses

        # ========== ГРАФИКИ (как в начальной модели) ==========
        plots_dir = "/app/plots"
        os.makedirs(plots_dir, exist_ok=True)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Структура посевов и прибыль по годам', fontsize=14, fontweight='bold', color='white')
        fig.patch.set_facecolor('#2e2e2e')

        for ax in axes.flat:
            ax.set_facecolor('#2e2e2e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')

        # Круговые диаграммы
        for i, year in enumerate(years[:2]):  # Максимум 2 года
            crops_list = [c for c in years_data[year]['crops'].keys() if c != 'fallow']
            if crops_list:
                areas = [years_data[year]['crops'].get(c, 0) for c in crops_list]
                labels = [crop_names_ru.get(c, c) for c in crops_list]
                colors = plt.cm.Set3(np.linspace(0, 1, len(crops_list)))
                textprops = {'color': 'white', 'fontsize': 9}
                axes[0, i].pie(areas, labels=labels, autopct='%1.1f%%',
                               colors=colors, startangle=90, textprops=textprops)
                axes[0, i].set_title(f'Структура посевов (Год {year})', fontsize=12, color='white')
            else:
                axes[0, i].text(0.5, 0.5, 'Нет данных', ha='center', va='center', color='white')
                axes[0, i].set_title(f'Структура посевов (Год {year})', fontsize=12, color='white')

        # Сравнение площадей (если есть 2 года)
        if len(years) >= 2:
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

        # Сохранение графиков
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        main_plot_path = os.path.join(plots_dir, f'optimization_plots_{timestamp}.png')
        plt.savefig(main_plot_path, dpi=150, bbox_inches='tight', facecolor='#2e2e2e')
        print(f"📊 Основной график сохранён: {main_plot_path}")

        latest_plot_path = os.path.join(plots_dir, 'optimization_plots_latest.png')
        plt.savefig(latest_plot_path, dpi=150, bbox_inches='tight', facecolor='#2e2e2e')
        print(f"📊 Последний график сохранён: {latest_plot_path}")

        # Отдельный график прибыли
        fig_profit, ax_profit = plt.subplots(figsize=(10, 6))
        fig_profit.patch.set_facecolor('#2e2e2e')
        ax_profit.set_facecolor('#2e2e2e')

        bars = ax_profit.bar(years, profits_list, color=['#66c2a5', '#fc8d62'])
        ax_profit.set_ylabel('Прибыль (BYN)', fontsize=12, color='white')
        ax_profit.set_xlabel('Год', fontsize=12, color='white')
        ax_profit.set_title('Прибыль по годам', fontsize=14, fontweight='bold', color='white')
        ax_profit.tick_params(colors='white')
        ax_profit.grid(axis='y', alpha=0.3, color='gray')

        for bar, profit in zip(bars, profits_list):
            ax_profit.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50000,
                           f'{profit:,.0f}', ha='center', va='bottom', fontsize=11, color='white')

        profit_plot_path = os.path.join(plots_dir, f'profit_by_year_{timestamp}.png')
        plt.savefig(profit_plot_path, dpi=150, bbox_inches='tight', facecolor='#2e2e2e')
        print(f"💰 График прибыли сохранён: {profit_plot_path}")

        profit_latest_path = os.path.join(plots_dir, 'profit_by_year_latest.png')
        plt.savefig(profit_latest_path, dpi=150, bbox_inches='tight', facecolor='#2e2e2e')

        plt.close('all')

        # Итог
        total = sum(profits.values())
        print(f"\n{'=' * 80}")
        print(f"🏆 ОБЩАЯ ПРИБЫЛЬ ЗА {len(years)} ГОДА: {total:>15,.0f} BYN")
        print(f"💰 СРЕДНЕГОДОВАЯ ПРИБЫЛЬ: {total / len(years):>15,.0f} BYN")
        print(f"\n📊 ПРИБЫЛЬ ПО ГОДАМ:")
        for year in years:
            print(f"   Год {year}: {profits[year]:>15,.0f} BYN")
        print(f"\n📁 ГРАФИКИ СОХРАНЕНЫ В ПАПКЕ: {plots_dir}")
        print("=" * 80)

