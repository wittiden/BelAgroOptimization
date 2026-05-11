from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, UniqueConstraint, ARRAY, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario
    from app.database.models.optimization import OptimizationResult
    from app.database.models.feed import FeedOutput


class Crop(Base):
    """Модель хранящая общие данные об урожае"""

    __tablename__ = "crops"

    __table_args__ = (
        Index("idx_crop_code", "code"),
        Index("idx_crop_permanent", "is_permanent"),
    )

    crop_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_permanent: Mapped[bool] = mapped_column(default=False)
    is_fallow: Mapped[bool] = mapped_column(default=False)

    sowing_months: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    harvest_months: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    vegetation_days: Mapped[int | None] = mapped_column(nullable=True)
    rotation_gap_years: Mapped[int] = mapped_column(default=1)

    scenario_data: Mapped[list["CropData"]] = relationship(back_populates="crop")
    feed_outputs: Mapped[list["FeedOutput"]] = relationship(back_populates="crop")

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
        return f"<Crop(code={self.code}, name={self.name})>"


class CropData(Base):
    """Модель хранящая технические данные об урожае"""

    __tablename__ = "crop_data"

    __table_args__ = (
        UniqueConstraint("scenario_id", "crop_id", name="uk_scenario_crop"),
        Index("idx_crop_data_scenario", "scenario_id"),
        Index("idx_crop_data_crop", "crop_id"),
    )

    crop_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    crop_id: Mapped[UUID] = mapped_column(ForeignKey("crops.crop_id"), nullable=False)

    base_yield_tha: Mapped[float] = mapped_column(Numeric(8, 2))
    price_byn_per_ts: Mapped[float] = mapped_column(Numeric(10, 2))
    cost_byn_per_ha: Mapped[float] = mapped_column(Numeric(10, 2))
    seed_cost_byn_per_ha: Mapped[float | None] = mapped_column(Numeric(10, 2))
    max_area_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)

    max_fert_kg: Mapped[float] = mapped_column(Numeric(8, 2), default=180.0)
    fert_cost_byn_per_kg: Mapped[float] = mapped_column(Numeric(8, 3), default=2.7)
    fert_response: Mapped[float] = mapped_column(Numeric(6, 4))

    optimal_temp: Mapped[float | None] = mapped_column(Numeric(5, 2))
    temp_sensitivity: Mapped[float | None] = mapped_column(Numeric(5, 4))
    water_requirement_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))

    scenario: Mapped["Scenario"] = relationship(back_populates="crop_data")
    crop: Mapped["Crop"] = relationship(back_populates="scenario_data")

    def __repr__(self) -> str:
        return f"<CropData(scenario={self.scenario_id}, crop={self.crop_id})>"


class CropAllocation(Base):
    """Модель хранящая данные о распределении урожая"""

    __tablename__ = "crop_allocations"

    __table_args__ = (
        Index("idx_result_crop", "result_id", "year", "field_code", "crop_code"),
        Index("idx_crop_alloc_result", "result_id"),
    )

    crop_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    field_code: Mapped[str] = mapped_column(String(50), nullable=False)
    crop_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2))
    yield_ts: Mapped[float] = mapped_column(Numeric(12, 2))
    fert_kg: Mapped[float] = mapped_column(Numeric(10, 2))

    result: Mapped["OptimizationResult"] = relationship(back_populates="crop_allocations")

    def __repr__(self) -> str:
        return f"<CropAllocation(year={self.year}, field={self.field_code}, crop={self.crop_code}, area={self.area_ha})>"
