from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, DECIMAL, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Scenario(Base):
    __tablename__ = "scenarios"

    # Просто UUID без PG_UUID
    scenario_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связи
    crop_data: Mapped[List["CropData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    livestock_data: Mapped[List["LivestockData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    weather_data: Mapped[List["WeatherData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    field_data: Mapped[List["FieldData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    feed_data: Mapped[List["FeedData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    feed_outputs: Mapped[List["FeedOutput"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    results: Mapped[List["OptimizationResult"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Scenario(id={self.scenario_id}, name={self.name}, active={self.is_active})>"


class Crop(Base):
    __tablename__ = "crops"

    crop_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_ru: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fallow: Mapped[bool] = mapped_column(Boolean, default=False)

    sowing_months: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    harvest_months: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    vegetation_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rotation_gap_years: Mapped[int] = mapped_column(Integer, default=1)

    scenario_data: Mapped[List["CropData"]] = relationship(back_populates="crop")
    feed_outputs: Mapped[List["FeedOutput"]] = relationship(back_populates="crop")

    @property
    def is_winter_crop(self) -> bool:
        if self.sowing_months:
            return any(month >= 9 or month <= 2 for month in self.sowing_months)
        return False

    @property
    def is_spring_crop(self) -> bool:
        if self.sowing_months:
            return any(3 <= month <= 6 for month in self.sowing_months)
        return False

    def __repr__(self) -> str:
        return f"<Crop(code={self.code}, name_ru={self.name_ru})>"

    __table_args__ = (
        Index("idx_crop_code", "code"),
        Index("idx_crop_permanent", "is_permanent"),
    )


class Field(Base):
    __tablename__ = "fields"

    field_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    area_ha: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    soil_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    soil_fertility: Mapped[float] = mapped_column(DECIMAL(5, 2), default=1.0)

    scenario_data: Mapped[List["FieldData"]] = relationship(back_populates="field")

    def __repr__(self) -> str:
        return f"<Field(code={self.code}, area_ha={self.area_ha})>"

    __table_args__ = (
        Index("idx_field_code", "code"),
    )


class CropData(Base):
    __tablename__ = "crop_data"

    crop_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    crop_id: Mapped[UUID] = mapped_column(ForeignKey("crops.crop_id"), nullable=False)

    base_yield_tha: Mapped[float] = mapped_column(DECIMAL(8, 2))
    price_byn_per_ts: Mapped[float] = mapped_column(DECIMAL(10, 2))
    cost_byn_per_ha: Mapped[float] = mapped_column(DECIMAL(10, 2))
    seed_cost_byn_per_ha: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))
    max_area_pct: Mapped[float] = mapped_column(DECIMAL(5, 2), default=100.0)

    max_fert_kg: Mapped[float] = mapped_column(DECIMAL(8, 2), default=180.0)
    fert_cost_byn_per_kg: Mapped[float] = mapped_column(DECIMAL(8, 3), default=2.7)
    fert_response: Mapped[float] = mapped_column(DECIMAL(6, 4))

    optimal_temp: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    temp_sensitivity: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4))
    water_requirement_mm: Mapped[Optional[float]] = mapped_column(DECIMAL(8, 2))

    scenario: Mapped["Scenario"] = relationship(back_populates="crop_data")
    crop: Mapped["Crop"] = relationship(back_populates="scenario_data")

    def __repr__(self) -> str:
        return f"<CropData(scenario={self.scenario_id}, crop={self.crop_id})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "crop_id", name="uk_scenario_crop"),
        Index("idx_crop_data_scenario", "scenario_id"),
        Index("idx_crop_data_crop", "crop_id"),
    )


class FieldData(Base):
    __tablename__ = "field_data"

    field_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    field_id: Mapped[UUID] = mapped_column(ForeignKey("fields.field_id"), nullable=False)
    area_ha: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    scenario: Mapped["Scenario"] = relationship(back_populates="field_data")
    field: Mapped["Field"] = relationship(back_populates="scenario_data")

    def __repr__(self) -> str:
        return f"<FieldData(scenario={self.scenario_id}, field={self.field_id}, area={self.area_ha})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "field_id", name="uk_scenario_field"),
        Index("idx_field_data_scenario", "scenario_id"),
        Index("idx_field_data_field", "field_id"),
    )


class WeatherData(Base):
    __tablename__ = "weather_data"

    weather_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature_avg: Mapped[float] = mapped_column(DECIMAL(5, 2))
    rainfall_mm: Mapped[float] = mapped_column(DECIMAL(8, 2))
    description: Mapped[Optional[str]] = mapped_column(String(100))

    scenario: Mapped["Scenario"] = relationship(back_populates="weather_data")

    def __repr__(self) -> str:
        return f"<WeatherData(year={self.year}, month={self.month}, temp={self.temperature_avg})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "year", "month", name="uk_scenario_year_month"),
        Index("idx_weather_scenario", "scenario_id"),
        Index("idx_weather_year_month", "year", "month"),
    )


class LivestockData(Base):
    __tablename__ = "livestock_data"

    livestock_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)

    min_heads: Mapped[int] = mapped_column(Integer, default=0)
    max_heads: Mapped[int] = mapped_column(Integer, nullable=False)

    base_yield_kg: Mapped[float] = mapped_column(DECIMAL(8, 2))
    max_yield_kg: Mapped[float] = mapped_column(DECIMAL(8, 2))
    price_byn_per_kg: Mapped[float] = mapped_column(DECIMAL(8, 3))

    cost_summer_byn: Mapped[float] = mapped_column(DECIMAL(10, 2))
    cost_winter_byn: Mapped[float] = mapped_column(DECIMAL(10, 2))
    energy_cost_winter_byn: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)

    scenario: Mapped["Scenario"] = relationship(back_populates="livestock_data")

    def __repr__(self) -> str:
        return f"<LivestockData(animal={self.animal_type}, min={self.min_heads}, max={self.max_heads})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "animal_type", name="uk_scenario_animal"),
        Index("idx_livestock_scenario", "scenario_id"),
        Index("idx_livestock_type", "animal_type"),
    )


class FeedData(Base):
    __tablename__ = "feed_data"

    feed_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)

    price_byn_per_centner: Mapped[float] = mapped_column(DECIMAL(8, 2))

    cow_need: Mapped[float] = mapped_column(DECIMAL(8, 2))
    cattle_need: Mapped[float] = mapped_column(DECIMAL(8, 2))
    pig_need: Mapped[float] = mapped_column(DECIMAL(8, 2))

    cow_max: Mapped[float] = mapped_column(DECIMAL(8, 2))
    cattle_max: Mapped[float] = mapped_column(DECIMAL(8, 2))
    pig_max: Mapped[float] = mapped_column(DECIMAL(8, 2))

    milk_efficiency: Mapped[float] = mapped_column(DECIMAL(6, 4))
    beef_efficiency: Mapped[float] = mapped_column(DECIMAL(6, 4))
    pork_efficiency: Mapped[float] = mapped_column(DECIMAL(6, 4))

    diminishing_beta: Mapped[float] = mapped_column(DECIMAL(6, 4), default=0.12)

    available_months: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)

    winter_price_multiplier: Mapped[float] = mapped_column(DECIMAL(4, 2), default=1.0)
    summer_price_multiplier: Mapped[float] = mapped_column(DECIMAL(4, 2), default=1.0)

    scenario: Mapped["Scenario"] = relationship(back_populates="feed_data")

    def __repr__(self) -> str:
        return f"<FeedData(type={self.feed_type}, price={self.price_byn_per_centner})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "feed_type", name="uk_scenario_feed"),
        Index("idx_feed_scenario", "scenario_id"),
        Index("idx_feed_type", "feed_type"),
    )


class FeedOutput(Base):
    __tablename__ = "feed_outputs"

    feed_output_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    crop_id: Mapped[UUID] = mapped_column(ForeignKey("crops.crop_id"), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)
    output_ratio: Mapped[float] = mapped_column(DECIMAL(6, 4))

    scenario: Mapped["Scenario"] = relationship(back_populates="feed_outputs")
    crop: Mapped["Crop"] = relationship(back_populates="feed_outputs")

    def __repr__(self) -> str:
        return f"<FeedOutput(crop={self.crop_id}, feed={self.feed_type}, ratio={self.output_ratio})>"

    __table_args__ = (
        UniqueConstraint("scenario_id", "crop_id", "feed_type", name="uk_scenario_crop_feed"),
        Index("idx_feed_output_scenario", "scenario_id"),
        Index("idx_feed_output_crop", "crop_id"),
    )


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    result_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    total_profit_byn: Mapped[float] = mapped_column(DECIMAL(20, 2))
    solver_status: Mapped[Optional[str]] = mapped_column(String(50))
    solution_time_sec: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    scenario: Mapped["Scenario"] = relationship(back_populates="results")
    crop_allocations: Mapped[List["CropAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    livestock_allocations: Mapped[List["LivestockAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    feed_allocations: Mapped[List["FeedAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    monthly_operations: Mapped[List["MonthlyOperation"]] = relationship(back_populates="result", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OptimizationResult(id={self.result_id}, profit={self.total_profit_byn})>"

    __table_args__ = (
        Index("idx_result_scenario", "scenario_id"),
        Index("idx_result_created", "created_at"),
    )


class CropAllocation(Base):
    __tablename__ = "crop_allocations"

    crop_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    field_code: Mapped[str] = mapped_column(String(50), nullable=False)
    crop_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_ha: Mapped[float] = mapped_column(DECIMAL(10, 2))
    yield_ts: Mapped[float] = mapped_column(DECIMAL(12, 2))
    fert_kg: Mapped[float] = mapped_column(DECIMAL(10, 2))

    result: Mapped["OptimizationResult"] = relationship(back_populates="crop_allocations")

    def __repr__(self) -> str:
        return f"<CropAllocation(year={self.year}, field={self.field_code}, crop={self.crop_code}, area={self.area_ha})>"

    __table_args__ = (
        Index("idx_result_crop", "result_id", "year", "field_code", "crop_code"),
        Index("idx_crop_alloc_result", "result_id"),
    )


class LivestockAllocation(Base):
    __tablename__ = "livestock_allocations"

    livestock_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    heads: Mapped[float] = mapped_column(DECIMAL(10, 2))
    milk_yield_summer_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))
    milk_yield_winter_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))

    result: Mapped["OptimizationResult"] = relationship(back_populates="livestock_allocations")

    def __repr__(self) -> str:
        return f"<LivestockAllocation(year={self.year}, type={self.animal_type}, heads={self.heads})>"

    __table_args__ = (
        Index("idx_result_livestock", "result_id", "year", "animal_type"),
        Index("idx_livestock_alloc_result", "result_id"),
    )


class FeedAllocation(Base):
    __tablename__ = "feed_allocations"

    feed_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)
    produced: Mapped[float] = mapped_column(DECIMAL(12, 2))
    consumed: Mapped[float] = mapped_column(DECIMAL(12, 2))
    surplus: Mapped[float] = mapped_column(DECIMAL(12, 2))

    result: Mapped["OptimizationResult"] = relationship(back_populates="feed_allocations")

    def __repr__(self) -> str:
        return f"<FeedAllocation(year={self.year}, type={self.feed_type}, surplus={self.surplus})>"

    __table_args__ = (
        Index("idx_result_feed", "result_id", "year", "feed_type"),
        Index("idx_feed_alloc_result", "result_id"),
    )


class MonthlyOperation(Base):
    __tablename__ = "monthly_operations"

    monthly_operation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    sowing_area_ha: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    harvesting_area_ha: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)

    tractor_hours: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    labor_hours: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)

    silage_consumed: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    hay_consumed: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    concentrate_consumed: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    pasture_consumed: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)

    result: Mapped["OptimizationResult"] = relationship(back_populates="monthly_operations")

    def __repr__(self) -> str:
        return f"<MonthlyOperation(year={self.year}, month={self.month})>"

    __table_args__ = (
        Index("idx_result_month", "result_id", "year", "month"),
        Index("idx_monthly_ops_result", "result_id"),
    )