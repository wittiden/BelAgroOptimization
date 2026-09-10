from typing import Generator
from sqlalchemy.orm import Session
from loguru import logger
from app.database.engine import session_factory


def get_db() -> Generator[Session | None, None, None]:
    """Provide a database session or None if database is unreachable."""
    session = None
    try:
        session = session_factory()
        yield session
    except Exception as e:
        logger.debug(f"Database unavailable ({e}). Using mock/in-memory data.")
        yield None
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
