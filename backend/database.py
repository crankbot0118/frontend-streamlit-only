"""SQLAlchemy engine + session factory.

Connection settings are loaded from the repo-root ``.env`` via ``config.settings``.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import database

_db = database()

engine = create_engine(
    _db.sqlalchemy_url,
    pool_size=_db.min_conn,
    max_overflow=max(0, _db.max_conn - _db.min_conn),
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
