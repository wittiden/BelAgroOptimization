from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from app.database.config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, echo=False)

engine = get_engine()


def get_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(engine)

session_factory = get_session_factory(engine)