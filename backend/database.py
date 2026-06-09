"""SQLAlchemy engine + session factory.

All DB interaction goes through ``get_db()``. Connection settings are read
from environment variables (loaded from ``~/.env`` if present).
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path.home() / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_database_url() -> str:
    user = _require_env("DB_USER")
    password = quote_plus(_require_env("DB_PASSWORD"))
    host = _require_env("DB_HOST")
    port = _require_env("DB_PORT")
    database = _require_env("DB_NAME")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


pool_size = int(os.getenv("DB_MIN_CONN", "1"))
max_connections = int(os.getenv("DB_MAX_CONN", "10"))

engine = create_engine(
    _build_database_url(),
    pool_size=pool_size,
    max_overflow=max(0, max_connections - pool_size),
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
