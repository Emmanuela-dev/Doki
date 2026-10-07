from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


def _sqlalchemy_database_url(url: str) -> str:
    """Make a Supabase/PostgreSQL URL explicit for the psycopg driver."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql+psycopg://"):
        return url
    raise ValueError(
        "DATABASE_URL must use a PostgreSQL URL, for example "
        "postgresql://user:password@host:5432/database"
    )


if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. Add the Supabase PostgreSQL connection "
        "string to backend/.env."
    )

DATABASE_URL = _sqlalchemy_database_url(settings.DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
