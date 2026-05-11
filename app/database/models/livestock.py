from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import ScenarioModel
    from app.database.models.optimization import OptimizationResultModel


class LivestockDataModel(Base):
    """Модель хранящая данные о животноводстве"""

    __tablename__ = "livestock_data"

    __table_args__ = (
        UniqueConstraint("scenario_id", "animal_type", name="uk_scenario_animal"),
        Index("idx_livestock_scenario", "scenario_id"),
        Index("idx_livestock_type", "animal_type"),
    )

    livestock_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)

    min_heads: Mapped[int] = mapped_column(default=0)
    max_heads: Mapped[int] = mapped_column(nullable=False)

    base_yield_kg: Mapped[float] = mapped_column(Numeric(8, 2))
    max_yield_kg: Mapped[float] = mapped_column(Numeric(8, 2))
    price_byn_per_kg: Mapped[float] = mapped_column(Numeric(8, 3))

    cost_summer_byn: Mapped[float] = mapped_column(Numeric(10, 2))
    cost_winter_byn: Mapped[float] = mapped_column(Numeric(10, 2))
    energy_cost_winter_byn: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    scenario: Mapped["ScenarioModel"] = relationship(back_populates="livestock_data")

    def __repr__(self) -> str:
        return f"<LivestockData(animal={self.animal_type}, min={self.min_heads}, max={self.max_heads})>"


class LivestockAllocationModel(Base):
    """Модель хранящая данные о распределении животноводства"""

    __tablename__ = "livestock_allocations"

    __table_args__ = (
        Index("idx_result_livestock", "result_id", "year", "animal_type"),
        Index("idx_livestock_alloc_result", "result_id"),
    )

    livestock_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    heads: Mapped[float] = mapped_column(Numeric(10, 2))
    milk_yield_summer_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    milk_yield_winter_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))

    result: Mapped["OptimizationResultModel"] = relationship(back_populates="livestock_allocations")

    def __repr__(self) -> str:
        return f"<LivestockAllocation(year={self.year}, type={self.animal_type}, heads={self.heads})>"
