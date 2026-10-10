import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL

# Handle Heroku / AWS Postgres URLs starting with postgres://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

def build_engine(url: str):
    connect_args = {}
    if "sqlite" in url:
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False
    )

engine = build_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes tables, enabling pgvector on Postgres or falling back to SQLite if Postgres is unavailable locally."""
    global engine, SessionLocal

    if "postgresql" in engine.url.drivername:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("Successfully connected to PostgreSQL and enabled pgvector extension.")
        except OperationalError as e:
            logger.warning(
                f"PostgreSQL server not detected at {engine.url.host}:{engine.url.port}. "
                "Gracefully falling back to local SQLite database (indian_stocks.db) for local evaluation."
            )
            # Rebind engine and session to SQLite
            db_url_fallback = "sqlite:///./indian_stocks.db"
            engine = build_engine(db_url_fallback)
            SessionLocal.configure(bind=engine)
        except Exception as e:
            logger.warning(f"Notice on PostgreSQL initialization: {e}")

    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
