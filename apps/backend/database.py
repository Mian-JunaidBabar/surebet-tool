from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create the data directory if it doesn't exist
os.makedirs("/app/data", exist_ok=True)

# Database URL - SQLite database stored in /app/data/surebets.db
# Note: For absolute paths in SQLite, use four slashes: sqlite:////absolute/path
SQLALCHEMY_DATABASE_URL = "sqlite:////app/data/surebets.db"

# Create SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Dependency function to get database session.
    This will be used in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()