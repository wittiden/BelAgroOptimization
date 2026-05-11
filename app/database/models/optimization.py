from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario
    from app.database.models.crop import CropAllocation
    from app.database.models.livestock import LivestockAllocation
    from app.database.models.feed import FeedAllocation
    from app.database.models.operation import MonthlyOperation


class OptimizationResult(Base):
    """Модель хранящая данные о результатах оптимизации"""

    __tablename__ = "optimization_results"

    __table_args__ = (
        Index("idx_result_scenario", "scenario_id"),
        Index("idx_result_created", "created_at"),
    )

    result_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    total_profit_byn: Mapped[float] = mapped_column(Numeric(20, 2))
    solver_status: Mapped[str | None] = mapped_column(String(50))
    solution_time_sec: Mapped[float | None] = mapped_column(Numeric(10, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    scenario: Mapped["Scenario"] = relationship(back_populates="results")
    crop_allocations: Mapped[list["CropAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    livestock_allocations: Mapped[list["LivestockAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    feed_allocations: Mapped[list["FeedAllocation"]] = relationship(back_populates="result", cascade="all, delete-orphan")
    monthly_operations: Mapped[list["MonthlyOperation"]] = relationship(back_populates="result", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<OptimizationResult(id={self.result_id}, profit={self.total_profit_byn})>"
