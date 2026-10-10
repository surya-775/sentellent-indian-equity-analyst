import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Stock, NewsArticle
from app.services.ingestion import StockIngestionPipeline

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()

def test_ingestion_idempotency_and_deduplication(test_db):
    pipeline = StockIngestionPipeline()
    ticker = "TCS"

    # First ingestion run
    res1 = pipeline.ingest_stock(test_db, ticker)
    assert res1["ticker"] == "TCS"
    assert res1["current_price_inr"] > 0
    assert res1["new_articles_indexed"] > 0

    articles_run1 = test_db.query(NewsArticle).filter(NewsArticle.ticker == "TCS").count()
    assert articles_run1 > 0

    # Second ingestion run on the same stock
    res2 = pipeline.ingest_stock(test_db, ticker)
    # Articles should NOT be duplicated due to SHA-256 fingerprint deduplication
    assert res2["new_articles_indexed"] == 0

    articles_run2 = test_db.query(NewsArticle).filter(NewsArticle.ticker == "TCS").count()
    assert articles_run1 == articles_run2, "Articles were duplicated during re-ingestion!"

def test_sentiment_and_event_extraction():
    pipeline = StockIngestionPipeline()
    title = "Reliance flags rising debt and aggressive capex commitments in energy sector"
    summary = "RIL balance sheet shows higher leverage and debt servicing scrutiny."
    analysis = pipeline.analyze_article_sentiment_and_events(title, summary)

    assert analysis["sentiment_score"] < 0
    assert analysis["sentiment_impact"] == "Negative"
    assert any("debt" in e.lower() for e in analysis["key_events"])
