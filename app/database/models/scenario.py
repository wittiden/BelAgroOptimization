from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.livestock import LivestockData
    from app.database.models.crop import CropData
    from app.database.models.weather import WeatherData
    from app.database.models.feed import FeedOutput, FeedData
    from app.database.models.field import FieldData
    from app.database.models.optimization import OptimizationResult


class Scenario(Base):
    """Модель хранящая данные о сценариях"""

    __tablename__ = "scenarios"

    scenario_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=False)

    crop_data: Mapped[list["CropData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    livestock_data: Mapped[list["LivestockData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    weather_data: Mapped[list["WeatherData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    field_data: Mapped[list["FieldData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    feed_data: Mapped[list["FeedData"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    feed_outputs: Mapped[list["FeedOutput"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    results: Mapped[list["OptimizationResult"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Scenario(id={self.scenario_id}, name={self.name}, active={self.is_active})>"
