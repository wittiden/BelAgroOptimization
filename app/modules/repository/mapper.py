from collections import defaultdict
from typing import Any, TYPE_CHECKING
from uuid import UUID

from app.modules.schemas import (
    LivestockParamsSchema, ModelDataSchema, WeatherYearSchema,
    CropParamsSchema, FieldParamsSchema, FeedPriceSchema, FeedNeedSchema
)

if TYPE_CHECKING:
    from app.modules.repository.queries import AgroQueriesRepository


class ModelDataMapper:
    """Маппер для преобразования orm -> schemas"""

    def __init__(self, repo: 'AgroQueriesRepository') -> None:
        self.repo = repo

    def build_from_active_scenario(self) -> dict[str, Any]:
        scenario = self.repo.select_scenario()

        if not scenario:
            raise ValueError("Нет активного сценария")
        return self.build_from_scenario(scenario.scenario_id)

    def build_from_scenario(self, scenario_id: UUID) -> dict[str, Any]:
        crops_data = self.repo.select_crops_data(scenario_id)
        fields_data = self.repo.select_fields_data(scenario_id)
        weather_data = self.repo.select_weathers_data(scenario_id)
        livestock_data = self.repo.select_livestocks_data(scenario_id)
        feed_data = self.repo.select_feeds_data(scenario_id)
        feed_outputs = self.repo.select_feeds_output(scenario_id)

        crops = {cd.crop.code: cd for cd in crops_data}
        fields = {fd.field.code: fd for fd in fields_data}
        livestock = {l.animal_type: l for l in livestock_data}
        feeds = {f.feed_type: f for f in feed_data}
        weather = self._build_weather(weather_data)

        if not crops:
            raise ValueError(f"Нет данных о культурах для сценария {scenario_id}")

        if not fields:
            raise ValueError(f"Нет данных о полях для сценария {scenario_id}")

        if not weather_data:
            raise ValueError(f"Нет погодных данных для сценария {scenario_id}")

        if not livestock:
            raise ValueError(f"Нет данных о животноводстве для сценария {scenario_id}")

        if not feeds:
            raise ValueError(f"Нет данных о кормах для сценария {scenario_id}")

        model_data = ModelDataSchema(
            crops=list(crops.keys()),
            fields=list(fields.keys()),
            years=sorted({w.year for w in weather_data}),
            feed_types=list(feeds.keys()),
            weather=weather,
            field_params={
                code: FieldParamsSchema(
                    area=float(f.area_ha),
                    soil_type=f.field.soil_type,
                    soil_fertility=float(f.field.soil_fertility)
                )
                for code, f in fields.items()
            },
            total_land=sum(float(f.area_ha) for f in fields.values()),
            crop_params={
                code: CropParamsSchema(
                    base_yield=float(cd.base_yield_tha),
                    price=float(cd.price_byn_per_ts),
                    cost=float(cd.cost_byn_per_ha),
                    seed_cost=float(cd.seed_cost_byn_per_ha) if cd.seed_cost_byn_per_ha else None,
                    fert_response=float(cd.fert_response)
                )
                for code, cd in crops.items()
            },

            max_fert=self._first_float(crops_data, 'max_fert_kg', 180.0),
            fert_cost=self._first_float(crops_data, 'fert_cost_byn_per_kg', 2.7),

            cows=self._build_livestock(livestock, 'cow'),
            cattle=self._build_livestock(livestock, 'cattle'),
            pigs=self._build_livestock(livestock, 'pig'),

            feed_price=FeedPriceSchema(
                summer=self._feed_price(feeds, 'summer'),
                winter=self._feed_price(feeds, 'winter')
            ),
            feed_need=FeedNeedSchema(
                summer=self._feed_need(feeds, 'summer'),
                winter=self._feed_need(feeds, 'winter')
            ),
            max_feed=self._extract_feed_dict(feeds, ['cow_max', 'cattle_max', 'pig_max']),
            feed_efficiency=self._extract_feed_dict(feeds, ['milk_efficiency', 'beef_efficiency', 'pork_efficiency']),
            diminishing_beta=self._diminishing_beta(feeds),
            feed_output=self._build_feed_output(feed_outputs),
        )

        return model_data.to_dict()

    def _extract(self, data: dict, attr: str, filter_none: bool = False) -> dict:
        """Извлечение атрибута из словаря объектов"""

        return {
            code: float(getattr(obj, attr))
            for code, obj in data.items()
            if getattr(obj, attr) is not None or not filter_none
        }

    def _first_float(self, data_list, attr: str, default: float) -> float:
        """Получение первого не-None значения из списка"""

        for obj in data_list:
            val = getattr(obj, attr, None)
            if val is not None:
                return float(val)
        return default

    def _build_weather(self, weather_data) -> dict[int, WeatherYearSchema]:
        """Агрегация помесячных погодных данных в годовые"""

        weather_by_year = defaultdict(lambda: {'temp': [], 'rain': []})
        for w in weather_data:
            weather_by_year[w.year]['temp'].append(float(w.temperature_avg))
            weather_by_year[w.year]['rain'].append(float(w.rainfall_mm))

        return {
            year: WeatherYearSchema(
                temp=sum(v['temp']) / len(v['temp']),
                rain=sum(v['rain']) / len(v['rain']),
                desc=f'Год {year}'
            )
            for year, v in weather_by_year.items()
        }

    def _build_livestock(self, livestock: dict, animal_type: str) -> LivestockParamsSchema:
        """Построение параметров животного"""

        data = livestock.get(animal_type)
        if not data:
            raise ValueError(f"Нет данных для {animal_type} в сценарии")

        return LivestockParamsSchema(
            min_heads=float(data.min_heads),
            max_heads=float(data.max_heads),
            base_yield=float(data.base_yield_kg),
            max_yield=float(data.max_yield_kg),
            price=float(data.price_byn_per_kg),
            cost_summer=float(data.cost_summer_byn),
            cost_winter=float(data.cost_winter_byn),
            energy_winter=float(data.energy_cost_winter_byn),
        )

    def _feed_price(self, feeds: dict, season: str) -> dict[str, float]:
        """Расчёт цен кормов с учётом сезонного коэффициента"""

        multiplier = f'{season}_price_multiplier'
        return {
            ft: float(f.price_byn_per_centner) * float(getattr(f, multiplier, 1.0))
            for ft, f in feeds.items()
        }

    def _feed_need(self, feeds: dict, season: str) -> dict[str, dict[str, float]]:
        """Расчёт потребности в кормах с учётом сезона"""

        coeff = 1.4 if season == 'winter' else 1.0
        return {
            animal: {
                ft: float(getattr(f, f'{animal}_need', 0)) * coeff
                for ft, f in feeds.items()
            }
            for animal in ['cow', 'cattle', 'pig']
        }

    def _extract_feed_dict(self, feeds: dict, keys: list) -> dict[str, dict[str, float]]:
        """Извлечение словаря данных по кормам для разных животных"""

        result = {key.split('_')[0]: {} for key in keys}
        for animal in ['cow', 'cattle', 'pig']:
            for key in keys:
                animal_key = key.split('_')[0]
                feed = feeds.get(animal)
                result[animal_key][animal] = float(getattr(feed, key, 0)) if feed else 0.0
        return result

    def _diminishing_beta(self, feeds: dict) -> dict[str, float]:
        """Параметры убывающей отдачи кормов"""

        if not feeds:
            raise ValueError("Нет данных о кормах")

        beta = next(iter(feeds.values())).diminishing_beta
        return {
            'milk': float(beta),
            'beef': float(beta),
            'pork': float(beta)
        }

    def _build_feed_output(self, feed_outputs) -> dict[str, dict[str, float]]:
        """Группировка выходов кормов по культурам"""

        result = defaultdict(dict)
        for fo in feed_outputs:
            result[fo.crop.code][fo.feed_type] = float(fo.output_ratio)
        return dict(result)
