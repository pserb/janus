from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable, or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/janus")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
