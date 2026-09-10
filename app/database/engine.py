from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from app.database.config import settings


from loguru import logger

_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_engine() -> Engine | None:
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(settings.database_url, echo=False)
        except Exception as e:
            logger.warning(f"Could not initialize database engine: {e}")
            return None
    return _engine


def session_factory():
    global _session_factory
    eng = get_engine()
    if eng is None:
        raise RuntimeError("Database engine not available")
    if _session_factory is None:
        _session_factory = sessionmaker(eng)
    return _session_factory()
