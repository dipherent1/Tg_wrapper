import os
from app.config.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = settings.DB_URL

# Create the SQLAlchemy engine
# The engine is the central source of connectivity to the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
# Our ORM models will inherit from this class.
Base = declarative_base()

# --- Dependency for FastAPI ---
def get_db():
    """
    A dependency that provides a database session for a single API request.
    It ensures the session is always closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()