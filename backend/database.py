"""SQLAlchemy engine + session factory.

Connection settings are loaded from the repo-root ``.env`` via ``config.settings``.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.errors import ConfigurationError
from config.logging import setup_logging
from config.settings import database

log = setup_logging("api.db")

try:
    _db = database()
    engine = create_engine(
        _db.sqlalchemy_url,
        pool_size=_db.min_conn,
        max_overflow=max(0, _db.max_conn - _db.min_conn),
        pool_pre_ping=True,
        echo=False,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
except ConfigurationError:
    raise
except SQLAlchemyError as exc:
    log.critical("Failed to create database engine: %s", exc)
    raise


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as exc:
        db.rollback()
        log.exception("Database session error")
        raise
    finally:
        db.close()
