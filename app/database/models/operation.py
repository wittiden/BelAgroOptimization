from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import Numeric, Index, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.optimization import OptimizationResultModel


class MonthlyOperationModel(Base):
    """Модель хранящая данные о календаре операций"""

    __tablename__ = "monthly_operations"

    __table_args__ = (
        Index("idx_result_month", "result_id", "year", "month"),
        Index("idx_monthly_ops_result", "result_id"),
    )

    monthly_operation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)

    sowing_area_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    harvesting_area_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    tractor_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    labor_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    silage_consumed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    hay_consumed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    concentrate_consumed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    pasture_consumed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    result: Mapped["OptimizationResultModel"] = relationship(back_populates="monthly_operations")

    def __repr__(self) -> str:
        return f"<MonthlyOperation(year={self.year}, month={self.month})>"
