from pydantic import BaseModel, computed_field
from typing import Any


class WeatherYearSchema(BaseModel):
    """Схема погоды"""

    temp: float
    rain: float
    desc: str


class LivestockParamsSchema(BaseModel):
    """Схема животноводства"""

    min_heads: float = 0
    max_heads: float
    base_yield: float
    max_yield: float
    price: float
    cost_summer: float
    cost_winter: float
    energy_winter: float = 0

    @computed_field
    @property
    def avg_cost(self) -> float:
        return (self.cost_summer * 183 + self.cost_winter * 182) / 365


class CropParamsSchema(BaseModel):
    """Схема параметров культур"""

    base_yield: float
    price: float
    cost: float
    seed_cost: float | None = None
    fert_response: float


class FieldParamsSchema(BaseModel):
    """Схема параметров полей"""

    area: float
    soil_type: str | None = None
    soil_fertility: float = 1.0


class FeedPriceSchema(BaseModel):
    """Схема цены кормов по сезонам"""

    summer: dict[str, float]
    winter: dict[str, float]


class FeedNeedSchema(BaseModel):
    """Схема потребности в кормах"""

    summer: dict[str, dict[str, float]]
    winter: dict[str, dict[str, float]]


class ModelDataSchema(BaseModel):
    """Все данные для оптимизационной модели"""

    crops: list[str]
    fields: list[str]
    years: list[int]
    feed_types: list[str]

    field_params: dict[str, FieldParamsSchema]
    total_land: float

    weather: dict[int, WeatherYearSchema]

    crop_params: dict[str, CropParamsSchema]

    max_fert: float = 180.0
    fert_cost: float = 2.7

    cows: LivestockParamsSchema
    cattle: LivestockParamsSchema
    pigs: LivestockParamsSchema

    feed_price: FeedPriceSchema
    feed_need: FeedNeedSchema
    max_feed: dict[str, dict[str, float]]
    feed_efficiency: dict[str, dict[str, float]]
    diminishing_beta: dict[str, float]
    feed_output: dict[str, dict[str, float]]

    #Константы
    summer_days: int = 183
    winter_days: int = 182
    winter_productivity_factor: dict[str, float] = {'milk': 0.82, 'beef': 0.85, 'pork': 0.88}
    grain_min_pct: float = 0.35
    feed_crop_min_pct: float = 0.20
    fallow_min_pct: float = 0.05
    potato_max_pct: float = 0.18
    rapeseed_max_pct: float = 0.15
    seasonal_adjustment: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        """Преобразование в словарь для pyomo"""

        result = self.model_dump(exclude={
            'crop_params', 'field_params', 'feed_price', 'feed_need',
            'cows', 'cattle', 'pigs'
        })

        for key in ['base_yield', 'price', 'cost', 'seed_cost', 'fert_response']:
            result[key] = {
                code: getattr(params, key)
                for code, params in self.crop_params.items()
                if getattr(params, key) is not None
            }

        result['field_area'] = {
            code: params.area for code, params in self.field_params.items()
        }

        result['feed_price_summer'] = self.feed_price.summer
        result['feed_price_winter'] = self.feed_price.winter

        result['base_feed_need_summer'] = self.feed_need.summer
        result['base_feed_need_winter'] = self.feed_need.winter

        result.update({
            'max_cows': self.cows.max_heads,
            'max_cattle': self.cattle.max_heads,
            'max_pigs': self.pigs.max_heads,
            'min_cows': self.cows.min_heads,
            'min_cattle': self.cattle.min_heads,
            'min_pigs': self.pigs.min_heads,
            'base_milk_yield': self.cows.base_yield,
            'base_beef_yield': self.cattle.base_yield,
            'base_pork_yield': self.pigs.base_yield,
            'max_milk_yield': self.cows.max_yield,
            'max_beef_yield': self.cattle.max_yield,
            'max_pork_yield': self.pigs.max_yield,
            'milk_price': self.cows.price,
            'beef_price': self.cattle.price,
            'pork_price': self.pigs.price,
            'cow_cost_summer': self.cows.cost_summer,
            'cow_cost_winter': self.cows.cost_winter,
            'cattle_cost_summer': self.cattle.cost_summer,
            'cattle_cost_winter': self.cattle.cost_winter,
            'pig_cost_summer': self.pigs.cost_summer,
            'pig_cost_winter': self.pigs.cost_winter,
            'energy_cost_cow_winter': self.cows.energy_winter,
            'energy_cost_cattle_winter': self.cattle.energy_winter,
            'energy_cost_pig_winter': self.pigs.energy_winter,
        })

        return result
