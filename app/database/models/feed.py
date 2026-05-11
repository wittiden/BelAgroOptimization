from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, UniqueConstraint, ARRAY, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario
    from app.database.models.optimization import OptimizationResult
    from app.database.models.crop import Crop


class FeedData(Base):
    """Модель хранящая данные о корме"""

    __tablename__ = "feed_data"

    __table_args__ = (
        UniqueConstraint("scenario_id", "feed_type", name="uk_scenario_feed"),
        Index("idx_feed_scenario", "scenario_id"),
        Index("idx_feed_type", "feed_type"),
    )

    feed_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)

    price_byn_per_centner: Mapped[float] = mapped_column(Numeric(8, 2))

    cow_need: Mapped[float] = mapped_column(Numeric(8, 2))
    cattle_need: Mapped[float] = mapped_column(Numeric(8, 2))
    pig_need: Mapped[float] = mapped_column(Numeric(8, 2))

    cow_max: Mapped[float] = mapped_column(Numeric(8, 2))
    cattle_max: Mapped[float] = mapped_column(Numeric(8, 2))
    pig_max: Mapped[float] = mapped_column(Numeric(8, 2))

    milk_efficiency: Mapped[float] = mapped_column(Numeric(6, 4))
    beef_efficiency: Mapped[float] = mapped_column(Numeric(6, 4))
    pork_efficiency: Mapped[float] = mapped_column(Numeric(6, 4))

    diminishing_beta: Mapped[float] = mapped_column(Numeric(6, 4), default=0.12)

    available_months: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)

    winter_price_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0)
    summer_price_multiplier: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0)

    scenario: Mapped["Scenario"] = relationship(back_populates="feed_data")

    def __repr__(self) -> str:
        return f"<FeedData(type={self.feed_type}, price={self.price_byn_per_centner})>"


class FeedOutput(Base):
    """Модель хранящая выводимые данные о корме"""

    __tablename__ = "feed_outputs"

    __table_args__ = (
        UniqueConstraint("scenario_id", "crop_id", "feed_type", name="uk_scenario_crop_feed"),
        Index("idx_feed_output_scenario", "scenario_id"),
        Index("idx_feed_output_crop", "crop_id"),
    )

    feed_output_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    crop_id: Mapped[UUID] = mapped_column(ForeignKey("crops.crop_id"), nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)
    output_ratio: Mapped[float] = mapped_column(Numeric(6, 4))

    scenario: Mapped["Scenario"] = relationship(back_populates="feed_outputs")
    crop: Mapped["Crop"] = relationship(back_populates="feed_outputs")

    def __repr__(self) -> str:
        return f"<FeedOutput(crop={self.crop_id}, feed={self.feed_type}, ratio={self.output_ratio})>"


class FeedAllocation(Base):
    """Модель хранящая данные о распределении корма"""

    __tablename__ = "feed_allocations"

    __table_args__ = (
        Index("idx_result_feed", "result_id", "year", "feed_type"),
        Index("idx_feed_alloc_result", "result_id"),
    )

    feed_allocation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("optimization_results.result_id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False)
    produced: Mapped[float] = mapped_column(Numeric(12, 2))
    consumed: Mapped[float] = mapped_column(Numeric(12, 2))
    surplus: Mapped[float] = mapped_column(Numeric(12, 2))

    result: Mapped["OptimizationResult"] = relationship(back_populates="feed_allocations")

    def __repr__(self) -> str:
        return f"<FeedAllocation(year={self.year}, type={self.feed_type}, surplus={self.surplus})>"

