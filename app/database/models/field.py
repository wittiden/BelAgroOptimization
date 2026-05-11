from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, Numeric, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.scenario import Scenario


class Field(Base):
    """Модель хранящая сведения о полях"""

    __tablename__ = "fields"

    __table_args__ = (
        Index("idx_field_code", "code"),
    )

    field_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    soil_fertility: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)

    scenario_data: Mapped[list["FieldData"]] = relationship(back_populates="field")

    def __repr__(self) -> str:
        return f"<Field(code={self.code}, area_ha={self.area_ha})>"


class FieldData(Base):
    """Модель хранящая данные о полях"""

    __tablename__ = "field_data"

    __table_args__ = (
        UniqueConstraint("scenario_id", "field_id", name="uk_scenario_field"),
        Index("idx_field_data_scenario", "scenario_id"),
        Index("idx_field_data_field", "field_id"),
    )

    field_data_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(ForeignKey("scenarios.scenario_id"), nullable=False)
    field_id: Mapped[UUID] = mapped_column(ForeignKey("fields.field_id"), nullable=False)
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    scenario: Mapped["Scenario"] = relationship(back_populates="field_data")
    field: Mapped["Field"] = relationship(back_populates="scenario_data")


    def __repr__(self) -> str:
        return f"<FieldData(scenario={self.scenario_id}, field={self.field_id}, area={self.area_ha})>"
