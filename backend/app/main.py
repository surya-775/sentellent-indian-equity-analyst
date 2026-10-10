import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db, SessionLocal
from app.db.models import Stock, User
from app.api.auth import router as auth_router
from app.api.routes import router as api_router
from app.services.ingestion import ingestion_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables and pre-seed initial stock universe
    logger.info("Initializing Database and pgvector...")
    init_db()

    db = SessionLocal()
    try:
        # Seed test evaluator user
        for test_email in settings.TEST_USERS:
            existing_user = db.query(User).filter(User.email == test_email).first()
            if not existing_user:
                db.add(User(email=test_email, name="Sentellent Evaluator", is_active=True))
        db.commit()

        # Seed initial Indian equities if table is empty
        stock_count = db.query(Stock).count()
        if stock_count == 0:
            logger.info("Database empty: Ingesting initial Indian stock universe (RELIANCE, TCS, HDFCBANK, INFY)...")
            initial_tickers = ["RELIANCE", "TCS", "HDFCBANK", "INFY"]
            for ticker in initial_tickers:
                try:
                    ingestion_pipeline.ingest_stock(db, ticker)
                except Exception as e:
                    logger.warning(f"Error seeding {ticker}: {e}")
            logger.info("Initial stock seeding complete.")
    finally:
        db.close()

    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Contextual Agentic AI Indian-Equity Analyst (RAG) with LangGraph & pgvector",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "online"
    }
