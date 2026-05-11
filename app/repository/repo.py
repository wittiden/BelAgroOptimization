# app/database/repository.py

from uuid import UUID
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models.Scenario import (
    Scenario, CropData, FieldData, WeatherData,
    LivestockData, FeedData, FeedOutput
)


class AgroRepository:
    """Репозиторий для загрузки данных из БД в оптимизационную модель"""

    def __init__(self, session: Session):
        self.session = session

    def get_active_scenario(self) -> Optional[Scenario]:
        """Получение активного сценария"""
        return self.session.execute(
            select(Scenario).where(Scenario.is_active == True)
        ).scalar_one_or_none()

    def get_scenario_by_id(self, scenario_id: UUID) -> Optional[Scenario]:
        """Получение сценария по ID"""
        return self.session.get(Scenario, scenario_id)

    def get_all_crop_data(self, scenario_id: UUID) -> List[CropData]:
        """Получение данных по всем культурам для сценария"""
        return self.session.execute(
            select(CropData).where(CropData.scenario_id == scenario_id)
        ).scalars().all()

    def get_all_field_data(self, scenario_id: UUID) -> List[FieldData]:
        """Получение данных по всем полям для сценария"""
        return self.session.execute(
            select(FieldData).where(FieldData.scenario_id == scenario_id)
        ).scalars().all()

    def get_all_weather_data(self, scenario_id: UUID) -> List[WeatherData]:
        """Получение погодных данных для сценария"""
        return self.session.execute(
            select(WeatherData).where(WeatherData.scenario_id == scenario_id)
        ).scalars().all()

    def get_all_livestock_data(self, scenario_id: UUID) -> List[LivestockData]:
        """Получение данных по животноводству для сценария"""
        return self.session.execute(
            select(LivestockData).where(LivestockData.scenario_id == scenario_id)
        ).scalars().all()

    def get_all_feed_data(self, scenario_id: UUID) -> List[FeedData]:
        """Получение данных по кормам для сценария"""
        return self.session.execute(
            select(FeedData).where(FeedData.scenario_id == scenario_id)
        ).scalars().all()

    def get_all_feed_outputs(self, scenario_id: UUID) -> List[FeedOutput]:
        """Получение данных по выходу кормов из культур"""
        return self.session.execute(
            select(FeedOutput).where(FeedOutput.scenario_id == scenario_id)
        ).scalars().all()


class ModelDataBuilder:
    """Построитель данных для модели из репозитория"""

    def __init__(self, repo: AgroRepository):
        self.repo = repo

    def build_from_active_scenario(self) -> Dict[str, Any]:
        """Построение данных из активного сценария"""
        scenario = self.repo.get_active_scenario()
        if not scenario:
            raise ValueError("Нет активного сценария")
        return self.build_from_scenario(scenario.scenario_id)

    def build_from_scenario(self, scenario_id: UUID) -> Dict[str, Any]:
        """Построение данных для модели по ID сценария"""

        # Загружаем все данные
        crop_data_list = self.repo.get_all_crop_data(scenario_id)
        field_data_list = self.repo.get_all_field_data(scenario_id)
        weather_data_list = self.repo.get_all_weather_data(scenario_id)
        livestock_data_list = self.repo.get_all_livestock_data(scenario_id)
        feed_data_list = self.repo.get_all_feed_data(scenario_id)
        feed_outputs = self.repo.get_all_feed_outputs(scenario_id)

        # Строим словари для быстрого доступа
        crops = {cd.crop.code: cd for cd in crop_data_list}
        fields = {fd.field.code: fd for fd in field_data_list}

        # Погода по годам
        weather_by_year: Dict[int, Dict[int, Dict[str, float]]] = {}
        for w in weather_data_list:
            if w.year not in weather_by_year:
                weather_by_year[w.year] = {}
            weather_by_year[w.year][w.month] = {
                'temp': float(w.temperature_avg),
                'rain': float(w.rainfall_mm)
            }

        # Животноводство по типам
        livestock_by_type = {l.animal_type: l for l in livestock_data_list}

        # Корма по типам
        feed_by_type = {f.feed_type: f for f in feed_data_list}

        # Выход кормов
        feed_output_by_crop: Dict[str, Dict[str, float]] = {}
        for fo in feed_outputs:
            crop_code = fo.crop.code
            if crop_code not in feed_output_by_crop:
                feed_output_by_crop[crop_code] = {}
            feed_output_by_crop[crop_code][fo.feed_type] = float(fo.output_ratio)

        # Собираем данные для модели
        return {
            # ========== ОСНОВНЫЕ МНОЖЕСТВА ==========
            'crops': [crop.crop.code for crop in crop_data_list],
            'fields': [field.field.code for field in field_data_list],
            'years': list(weather_by_year.keys()),
            'feed_types': list(feed_by_type.keys()),

            # ========== ГЕОГРАФИЯ ==========
            'field_area': {field.field.code: float(field.area_ha) for field in field_data_list},
            'total_land': sum(float(field.area_ha) for field in field_data_list),

            # ========== ПОГОДА (усреднённая по году) ==========
            'weather': {
                year: {
                    'temp': sum(m['temp'] for m in months.values()) / len(months),
                    'rain': sum(m['rain'] for m in months.values()) / len(months),
                    'desc': f'Год {year}'
                }
                for year, months in weather_by_year.items()
            },

            # ========== ПАРАМЕТРЫ КУЛЬТУР ==========
            'base_yield': {code: float(cd.base_yield_tha) for code, cd in crops.items()},
            'price': {code: float(cd.price_byn_per_ts) for code, cd in crops.items()},
            'cost': {code: float(cd.cost_byn_per_ha) for code, cd in crops.items()},
            'seed_cost': {code: float(cd.seed_cost_byn_per_ha) for code, cd in crops.items() if
                          cd.seed_cost_byn_per_ha},

            # ========== УДОБРЕНИЯ ==========
            'max_fert': float(crop_data_list[0].max_fert_kg) if crop_data_list else 180.0,
            'fert_cost': float(crop_data_list[0].fert_cost_byn_per_kg) if crop_data_list else 2.7,
            'fert_response': {code: float(cd.fert_response) for code, cd in crops.items()},

            # ========== ЖИВОТНОВОДСТВО ==========
            'max_cows': float(
                livestock_by_type.get('cow', LivestockData()).max_heads) if 'cow' in livestock_by_type else 1200.0,
            'max_cattle': float(livestock_by_type.get('cattle',
                                                      LivestockData()).max_heads) if 'cattle' in livestock_by_type else 1800.0,
            'max_pigs': float(
                livestock_by_type.get('pig', LivestockData()).max_heads) if 'pig' in livestock_by_type else 4000.0,

            'min_cows': float(
                livestock_by_type.get('cow', LivestockData()).min_heads) if 'cow' in livestock_by_type else 200.0,
            'min_cattle': float(
                livestock_by_type.get('cattle', LivestockData()).min_heads) if 'cattle' in livestock_by_type else 200.0,
            'min_pigs': float(
                livestock_by_type.get('pig', LivestockData()).min_heads) if 'pig' in livestock_by_type else 500.0,

            'base_milk_yield': float(
                livestock_by_type.get('cow', LivestockData()).base_yield_kg) if 'cow' in livestock_by_type else 5000.0,
            'base_beef_yield': float(livestock_by_type.get('cattle',
                                                           LivestockData()).base_yield_kg) if 'cattle' in livestock_by_type else 250.0,
            'base_pork_yield': float(
                livestock_by_type.get('pig', LivestockData()).base_yield_kg) if 'pig' in livestock_by_type else 100.0,

            'max_milk_yield': float(
                livestock_by_type.get('cow', LivestockData()).max_yield_kg) if 'cow' in livestock_by_type else 8000.0,
            'max_beef_yield': float(livestock_by_type.get('cattle',
                                                          LivestockData()).max_yield_kg) if 'cattle' in livestock_by_type else 380.0,
            'max_pork_yield': float(
                livestock_by_type.get('pig', LivestockData()).max_yield_kg) if 'pig' in livestock_by_type else 160.0,

            'milk_price': float(
                livestock_by_type.get('cow', LivestockData()).price_byn_per_kg) if 'cow' in livestock_by_type else 1.9,
            'beef_price': float(livestock_by_type.get('cattle',
                                                      LivestockData()).price_byn_per_kg) if 'cattle' in livestock_by_type else 8.2,
            'pork_price': float(
                livestock_by_type.get('pig', LivestockData()).price_byn_per_kg) if 'pig' in livestock_by_type else 7.0,

            'cow_cost_summer': float(livestock_by_type.get('cow',
                                                           LivestockData()).cost_summer_byn) if 'cow' in livestock_by_type else 3800.0,
            'cow_cost_winter': float(livestock_by_type.get('cow',
                                                           LivestockData()).cost_winter_byn) if 'cow' in livestock_by_type else 5200.0,
            'cattle_cost_summer': float(livestock_by_type.get('cattle',
                                                              LivestockData()).cost_summer_byn) if 'cattle' in livestock_by_type else 2200.0,
            'cattle_cost_winter': float(livestock_by_type.get('cattle',
                                                              LivestockData()).cost_winter_byn) if 'cattle' in livestock_by_type else 3000.0,
            'pig_cost_summer': float(livestock_by_type.get('pig',
                                                           LivestockData()).cost_summer_byn) if 'pig' in livestock_by_type else 1000.0,
            'pig_cost_winter': float(livestock_by_type.get('pig',
                                                           LivestockData()).cost_winter_byn) if 'pig' in livestock_by_type else 1500.0,

            'energy_cost_cow_winter': float(livestock_by_type.get('cow',
                                                                  LivestockData()).energy_cost_winter_byn) if 'cow' in livestock_by_type else 800.0,
            'energy_cost_cattle_winter': float(livestock_by_type.get('cattle',
                                                                     LivestockData()).energy_cost_winter_byn) if 'cattle' in livestock_by_type else 400.0,
            'energy_cost_pig_winter': float(livestock_by_type.get('pig',
                                                                  LivestockData()).energy_cost_winter_byn) if 'pig' in livestock_by_type else 300.0,

            # ========== КОРМА ==========
            'feed_price_summer': {ft: float(f.price_byn_per_centner) * float(f.summer_price_multiplier) for ft, f in
                                  feed_by_type.items()},
            'feed_price_winter': {ft: float(f.price_byn_per_centner) * float(f.winter_price_multiplier) for ft, f in
                                  feed_by_type.items()},

            'base_feed_need_summer': {
                'cow': {ft: float(f.cow_need) for ft, f in feed_by_type.items()},
                'cattle': {ft: float(f.cattle_need) for ft, f in feed_by_type.items()},
                'pig': {ft: float(f.pig_need) for ft, f in feed_by_type.items()}
            },
            'base_feed_need_winter': {
                'cow': {ft: float(f.cow_need) * 1.4 for ft, f in feed_by_type.items()},
                'cattle': {ft: float(f.cattle_need) * 1.3 for ft, f in feed_by_type.items()},
                'pig': {ft: float(f.pig_need) * 1.2 for ft, f in feed_by_type.items()}
            },

            'max_feed': {
                'cow': {ft: float(f.cow_max) for ft, f in feed_by_type.items()},
                'cattle': {ft: float(f.cattle_max) for ft, f in feed_by_type.items()},
                'pig': {ft: float(f.pig_max) for ft, f in feed_by_type.items()}
            },

            'feed_efficiency': {
                'milk': {ft: float(f.milk_efficiency) for ft, f in feed_by_type.items()},
                'beef': {ft: float(f.beef_efficiency) for ft, f in feed_by_type.items()},
                'pork': {ft: float(f.pork_efficiency) for ft, f in feed_by_type.items()}
            },

            'diminishing_beta': {
                'milk': float(next(iter(feed_by_type.values())).diminishing_beta) if feed_by_type else 0.12,
                'beef': float(next(iter(feed_by_type.values())).diminishing_beta) if feed_by_type else 0.15,
                'pork': float(next(iter(feed_by_type.values())).diminishing_beta) if feed_by_type else 0.18
            },

            'feed_output': feed_output_by_crop,

            # ========== СЕЗОННЫЕ КОЭФФИЦИЕНТЫ ==========
            'summer_days': 183,
            'winter_days': 182,

            'winter_productivity_factor': {
                'milk': 0.82, 'beef': 0.85, 'pork': 0.88
            },

            # ========== ОГРАНИЧЕНИЯ ==========
            'grain_min_pct': 0.35,
            'feed_crop_min_pct': 0.20,
            'fallow_min_pct': 0.05,
            'potato_max_pct': 0.18,
            'rapeseed_max_pct': 0.15,
            'seasonal_adjustment': 0.85
        }