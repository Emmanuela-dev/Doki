from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base


def _sqlalchemy_database_url(url: str) -> str:
    """Make a PostgreSQL URL explicit for the psycopg driver."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg://"):
        return url
    return url


DATABASE_URL = _sqlalchemy_database_url(settings.DATABASE_URL)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
