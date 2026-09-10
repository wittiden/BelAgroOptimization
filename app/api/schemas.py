from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field


# ==========================================
# СЦЕНАРИИ
# ==========================================

class ScenarioBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None


class ScenarioCreate(ScenarioBase):
    is_active: bool = False


class ScenarioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ScenarioItem(ScenarioBase):
    scenario_id: UUID
    is_active: bool
    created_at: datetime
    last_profit: float | None = None
    fields_count: int = 0
    crops_count: int = 0

    class Config:
        from_attributes = True


# ==========================================
# ПОЛЯ
# ==========================================

class FieldDto(BaseModel):
    field_id: UUID
    code: str
    area_ha: float
    soil_type: str | None = None
    soil_fertility: float = 1.0

    class Config:
        from_attributes = True


class FieldDataDto(BaseModel):
    field_data_id: UUID
    scenario_id: UUID
    field_id: UUID
    code: str
    area_ha: float
    soil_type: str | None = None
    soil_fertility: float = 1.0


class FieldUpdateDto(BaseModel):
    area_ha: float | None = None
    soil_type: str | None = None
    soil_fertility: float | None = None


# ==========================================
# КУЛЬТУРЫ
# ==========================================

class CropDataDto(BaseModel):
    crop_data_id: UUID
    crop_id: UUID
    code: str
    name: str | None = None
    base_yield_tha: float
    price_byn_per_ts: float
    cost_byn_per_ha: float
    seed_cost_byn_per_ha: float | None = None
    max_area_pct: float = 100.0
    max_fert_kg: float = 180.0
    fert_cost_byn_per_kg: float = 2.7
    fert_response: float = 0.05
    sowing_months: list[int] | None = None
    harvest_months: list[int] | None = None
    vegetation_days: int | None = None
    rotation_gap_years: int = 1


class CropDataUpdateDto(BaseModel):
    base_yield_tha: float | None = None
    price_byn_per_ts: float | None = None
    cost_byn_per_ha: float | None = None
    seed_cost_byn_per_ha: float | None = None
    max_area_pct: float | None = None
    max_fert_kg: float | None = None
    fert_cost_byn_per_kg: float | None = None
    fert_response: float | None = None


# ==========================================
# ЖИВОТНОВОДСТВО
# ==========================================

class LivestockDataDto(BaseModel):
    livestock_data_id: UUID
    scenario_id: UUID
    animal_type: str
    min_heads: int
    max_heads: int
    base_yield_kg: float
    max_yield_kg: float
    price_byn_per_kg: float
    cost_summer_byn: float
    cost_winter_byn: float
    energy_cost_winter_byn: float


class LivestockUpdateDto(BaseModel):
    min_heads: int | None = None
    max_heads: int | None = None
    base_yield_kg: float | None = None
    max_yield_kg: float | None = None
    price_byn_per_kg: float | None = None
    cost_summer_byn: float | None = None
    cost_winter_byn: float | None = None
    energy_cost_winter_byn: float | None = None


# ==========================================
# КОРМА
# ==========================================

class FeedDataDto(BaseModel):
    feed_data_id: UUID
    scenario_id: UUID
    feed_type: str
    price_byn_per_centner: float
    cow_need: float
    cattle_need: float
    pig_need: float
    cow_max: float
    cattle_max: float
    pig_max: float
    milk_efficiency: float
    beef_efficiency: float
    pork_efficiency: float
    diminishing_beta: float = 0.12
    winter_price_multiplier: float = 1.0
    summer_price_multiplier: float = 1.0


class FeedUpdateDto(BaseModel):
    price_byn_per_centner: float | None = None
    cow_need: float | None = None
    cattle_need: float | None = None
    pig_need: float | None = None
    winter_price_multiplier: float | None = None
    summer_price_multiplier: float | None = None


class FeedOutputDto(BaseModel):
    feed_output_id: UUID
    crop_code: str
    feed_type: str
    output_ratio: float


# ==========================================
# ПОГОДА
# ==========================================

class WeatherDataDto(BaseModel):
    weather_data_id: UUID
    scenario_id: UUID
    year: int
    month: int
    temperature_avg: float
    rainfall_mm: float
    description: str | None = None


class WeatherYearSummaryDto(BaseModel):
    year: int
    temp_avg: float
    rain_total: float
    is_drought: bool


# ==========================================
# ОПТИМИЗАЦИЯ И РЕЗУЛЬТАТЫ
# ==========================================

class OptimizationRunRequest(BaseModel):
    scenario_id: UUID | None = None


class OptimizationJobStatus(BaseModel):
    job_id: str
    scenario_id: UUID
    status: str  # pending, running, completed, failed
    progress: int = 0
    message: str | None = None
    logs: list[str] = []
    started_at: datetime
    finished_at: datetime | None = None
    execution_time_sec: float | None = None


class CropAllocationDto(BaseModel):
    year: int
    field_code: str
    crop_code: str
    area_ha: float
    yield_ts: float
    fert_kg: float


class LivestockAllocationDto(BaseModel):
    year: int
    animal_type: str
    heads: float
    milk_yield_summer_kg: float | None = None
    milk_yield_winter_kg: float | None = None


class FeedAllocationDto(BaseModel):
    year: int
    feed_type: str
    produced: float
    consumed: float
    surplus: float


class MonthlyOperationDto(BaseModel):
    year: int
    month: int
    sowing_area_ha: float
    harvesting_area_ha: float
    tractor_hours: float
    labor_hours: float
    silage_consumed: float
    hay_consumed: float
    concentrate_consumed: float
    pasture_consumed: float


class YearResultDto(BaseModel):
    year: int
    crop_profit: float
    livestock_profit: float
    total_profit: float
    weather_temp: float | None = None
    weather_rain: float | None = None
    crop_areas: dict[str, float] = {}
    crop_profits: dict[str, float] = {}
    livestock_profits: dict[str, float] = {}
    livestock_heads: dict[str, float] = {}
    feed_balances: dict[str, dict[str, float]] = {}


class OptimizationResultDto(BaseModel):
    result_id: UUID
    scenario_id: UUID
    scenario_name: str
    total_profit_byn: float
    avg_annual_profit_byn: float
    solver_status: str
    solution_time_sec: float | None = None
    created_at: datetime
    years: list[YearResultDto] = []
    crop_allocations: list[CropAllocationDto] = []
    livestock_allocations: list[LivestockAllocationDto] = []
    feed_allocations: list[FeedAllocationDto] = []
    plots: list[str] = []


class DashboardSummaryDto(BaseModel):
    active_scenario_id: UUID | None = None
    active_scenario_name: str | None = None
    total_land_ha: float = 0
    fields_count: int = 0
    crops_count: int = 0
    livestock_types_count: int = 0
    last_optimized_at: datetime | None = None
    last_total_profit: float | None = None
    last_avg_profit: float | None = None
    solver_status: str | None = None
