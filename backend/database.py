"""
SQLAlchemy database engine, session management, and Base class.

Uses SQLite for zero-config persistence.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DB_PATH

# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base class for ORM models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependency for FastAPI route injection
# ---------------------------------------------------------------------------
def get_db():
    """Yield a database session, ensuring it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
