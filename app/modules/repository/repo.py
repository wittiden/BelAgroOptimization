from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models.crop import CropDataModel
from app.database.models.feed import FeedDataModel, FeedOutputModel
from app.database.models.field import FieldDataModel
from app.database.models.livestock import LivestockDataModel
from app.database.models.scenario import ScenarioModel
from app.database.models.weather import WeatherDataModel


class AgroQueriesRepository:
    """Репозиторий select запросов в бд"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def select_scenario(self) -> 'ScenarioModel | None':
        return self._session.execute(select(ScenarioModel).where(ScenarioModel.is_active)).scalar_one_or_none()

    def select_scenario_by_id(self, scenario_id: UUID) -> 'ScenarioModel | None':
        return self._session.get(ScenarioModel, scenario_id)

    def select_crops_data(self, scenario_id: UUID) -> list['CropDataModel']:
        return list(self._session.execute(select(CropDataModel).where(CropDataModel.scenario_id == scenario_id)).scalars().all())

    def select_fields_data(self, scenario_id: UUID) -> list['FieldDataModel']:
        return list(self._session.execute(select(FieldDataModel).where(FieldDataModel.scenario_id == scenario_id)).scalars().all())

    def select_weathers_data(self, scenario_id: UUID) -> list['WeatherDataModel']:
        return list(self._session.execute(select(WeatherDataModel).where(WeatherDataModel.scenario_id == scenario_id)).scalars().all())

    def select_livestocks_data(self, scenario_id: UUID) -> list['LivestockDataModel']:
        return list(self._session.execute(select(LivestockDataModel).where(LivestockDataModel.scenario_id == scenario_id)).scalars().all())

    def select_feeds_data(self, scenario_id: UUID) -> list['FeedDataModel']:
        return list(self._session.execute(select(FeedDataModel).where(FeedDataModel.scenario_id == scenario_id)).scalars().all())

    def select_feeds_output(self, scenario_id: UUID) -> list['FeedOutputModel']:
        return list(self._session.execute(select(FeedOutputModel).where(FeedOutputModel.scenario_id == scenario_id)).scalars().all())
