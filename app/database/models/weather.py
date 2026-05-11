from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario


class WeatherData(Base):
    """Модель хранящая данные о погоде"""

    __tablename__ = "weather_data"

    __table_args__ = (
        UniqueConstraint("scenario_id", "year", "month", name="uk_scenario_year_month"),
        Index("idx_weather_scenario", "scenario_id"),
        Index("idx_weather_year_month", "year", "month"),
    )

    weather_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    temperature_avg: Mapped[float] = mapped_column(Numeric(5, 2))
    rainfall_mm: Mapped[float] = mapped_column(Numeric(8, 2))
    description: Mapped[str | None] = mapped_column(String(100))

    scenario: Mapped["Scenario"] = relationship(back_populates="weather_data")

    def __repr__(self) -> str:
        return f"<WeatherData(year={self.year}, month={self.month}, temp={self.temperature_avg})>"
