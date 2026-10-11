from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


engine= create_engine(
    settings.database_url
)

session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Get a database session."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()