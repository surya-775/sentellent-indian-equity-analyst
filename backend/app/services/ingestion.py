import os
import re
import json
import logging

import datetime
import threading
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models import Stock, NewsArticle
from app.services.market_data import market_data_service
from app.services.news_feed import news_feed_service
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

# Mutex locks per ticker to guarantee race-condition free concurrent ingestion
_ticker_locks: Dict[str, threading.Lock] = {}
_lock_access = threading.Lock()

def _get_ticker_lock(ticker: str) -> threading.Lock:
    clean = ticker.upper().strip()
    with _lock_access:
        if clean not in _ticker_locks:
            _ticker_locks[clean] = threading.Lock()
        return _ticker_locks[clean]

class StockIngestionPipeline:
    def __init__(self):
        self.market_data = market_data_service
        self.news_feed = news_feed_service
        self.vector_store = vector_store_service

    def analyze_article_sentiment_and_events(self, title: str, summary: str) -> Dict[str, Any]:
        """
        Extracts sentiment score (-1.0 to +1.0) and key events (e.g. 'Rising debt', 'Capex expansion').
        Uses LLM if available, with robust, rule-based financial NLP fallback for zero-latency execution.
        """
        text = f"{title} {summary}".lower()
        
        # Rule-based financial keyword weighting with regex word boundaries
        positive_cues = [r"\bexpansion\b", r"\bgrowth\b", r"\bprofit\b", r"\bsurge\b", r"\bsurges\b", r"\bdeal\b", r"\bdividend\b", r"\bcontract\b", r"\brecord\b", r"\bjump\b", r"\bsoars\b", r"\bgain\b", r"\bgains\b", r"\bup\b"]
        negative_cues = [r"\bdebt\b", r"\bleverage\b", r"\brising debt\b", r"\blosses\b", r"\bloss\b", r"\bslump\b", r"\bslumps\b", r"\bfraud\b", r"\bpenalty\b", r"\bcaution\b", r"\bdowngrade\b", r"\bprobe\b", r"\bfall\b", r"\bdeclines\b", r"\bdown\b", r"\bdefault\b", r"\bscam\b", r"\bnpa\b"]

        pos_count = sum(1 for p in positive_cues if re.search(p, text))
        neg_count = sum(1 for p in negative_cues if re.search(p, text))

        score = 0.0
        if pos_count > neg_count:
            score = min(0.3 + 0.15 * (pos_count - neg_count), 0.95)
        elif neg_count > pos_count:
            score = max(-0.3 - 0.15 * (neg_count - pos_count), -0.95)
        else:
            score = 0.05

        impact = "Positive" if score > 0.2 else ("Negative" if score < -0.2 else "Neutral")

        
        events = []
        if "debt" in text or "rising debt" in text:
            events.append("Rising debt / leverage scrutiny")
        if "dividend" in text:
            events.append("Dividend announcement")
        if "deal" in text or "contract" in text:
            events.append("Major deal / contract win")
        if "capex" in text or "expansion" in text:
            events.append("Capex / operational expansion")
        if "profit" in text or "earnings" in text or "margin" in text:
            events.append("Earnings & margin update")

        return {
            "sentiment_score": round(score, 2),
            "sentiment_impact": impact,
            "key_events": events or ["Operational updates"]
        }

    def ingest_stock(self, db: Session, ticker: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Idempotent, race-condition protected ingestion of an Indian stock ticker.
        1. Acquires ticker mutex lock.
        2. Fetches fundamentals (Screener + yfinance in INR).
        3. Upserts Stock record.
        4. Fetches recent RSS news, deduplicates via SHA-256 hashes.
        5. Embeds new articles and stores into vector store.
        6. Updates stock's rolling sentiment.
        """
        clean_ticker = ticker.upper().strip()
        lock = _get_ticker_lock(clean_ticker)

        with lock:
            logger.info(f"Starting ingestion for ticker: {clean_ticker}")
            
            # 1. Fetch Fundamentals
            fund_data = self.market_data.get_consolidated_fundamentals(clean_ticker)

            # 2. Upsert Stock record in DB
            stock = db.query(Stock).filter(Stock.ticker == clean_ticker).first()
            if not stock:
                stock = Stock(
                    ticker=clean_ticker,
                    name=fund_data.get("name", clean_ticker),
                    exchange=fund_data.get("exchange", "NSE"),
                    nse_id=fund_data.get("nse_id", clean_ticker),
                    bse_id=fund_data.get("bse_id", ""),
                    sector=fund_data.get("sector", "Diversified"),
                    current_price_inr=fund_data.get("current_price_inr", 0.0),
                    market_cap_crores_inr=fund_data.get("market_cap_crores_inr", 0.0),
                    pe_ratio=fund_data.get("pe_ratio"),
                    debt_to_equity=fund_data.get("debt_to_equity"),
                    dividend_yield_pct=fund_data.get("dividend_yield_pct"),
                    roce_pct=fund_data.get("roce_pct"),
                    roe_pct=fund_data.get("roe_pct"),
                    profit_growth_qoq_pct=fund_data.get("profit_growth_qoq_pct"),
                    last_ingested_at=datetime.datetime.utcnow()
                )
                db.add(stock)
            else:
                stock.name = fund_data.get("name", stock.name)
                stock.current_price_inr = fund_data.get("current_price_inr", stock.current_price_inr)
                stock.market_cap_crores_inr = fund_data.get("market_cap_crores_inr", stock.market_cap_crores_inr)
                stock.pe_ratio = fund_data.get("pe_ratio", stock.pe_ratio)
                stock.debt_to_equity = fund_data.get("debt_to_equity", stock.debt_to_equity)
                stock.dividend_yield_pct = fund_data.get("dividend_yield_pct", stock.dividend_yield_pct)
                stock.roce_pct = fund_data.get("roce_pct", stock.roce_pct)
                stock.roe_pct = fund_data.get("roe_pct", stock.roe_pct)
                stock.profit_growth_qoq_pct = fund_data.get("profit_growth_qoq_pct", stock.profit_growth_qoq_pct)
                stock.last_ingested_at = datetime.datetime.utcnow()

            db.commit()

            # 3. Fetch News Articles (Deduplicated via SHA-256)
            articles_data = self.news_feed.fetch_articles_for_ticker(clean_ticker)
            new_articles_count = 0

            for item in articles_data:
                article_hash = item["article_hash"]
                existing = db.query(NewsArticle).filter(NewsArticle.article_hash == article_hash).first()
                if existing:
                    continue # Skip duplicate article (idempotency guarantee)

                # Sentiment & Event analysis
                analysis = self.analyze_article_sentiment_and_events(
                    item.get("title", ""),
                    item.get("summary", "")
                )
                
                # Embedding text chunk
                chunk_text = f"Stock: {clean_ticker} ({stock.name})\nTitle: {item['title']}\nSource: {item['source']}\nSummary: {item['summary']}\nEvents: {', '.join(analysis['key_events'])}"
                embedding_vector = self.vector_store.embed_text(chunk_text)

                article = NewsArticle(
                    article_hash=article_hash,
                    ticker=clean_ticker,
                    title=item["title"],
                    url=item["url"],
                    source=item["source"],
                    published_at=item.get("published_at", datetime.datetime.utcnow()),
                    summary=item.get("summary", ""),
                    content_snippet=chunk_text[:500],
                    sentiment_score=analysis["sentiment_score"],
                    sentiment_impact=analysis["sentiment_impact"],
                    key_events=analysis["key_events"],
                    embedding=json.dumps(embedding_vector) if not ("postgresql" in str(db.bind.url)) else embedding_vector
                )
                db.add(article)
                new_articles_count += 1

            db.commit()

            # 4. Update rolling sentiment score for the stock
            recent_articles = db.query(NewsArticle).filter(NewsArticle.ticker == clean_ticker).order_by(NewsArticle.published_at.desc()).limit(10).all()
            if recent_articles:
                avg_sentiment = sum(a.sentiment_score for a in recent_articles) / len(recent_articles)
                stock.rolling_sentiment = round(avg_sentiment, 2)
                if stock.rolling_sentiment > 0.2:
                    stock.sentiment_label = "Bullish"
                elif stock.rolling_sentiment < -0.2:
                    stock.sentiment_label = "Bearish"
                else:
                    stock.sentiment_label = "Neutral"
                db.commit()

            logger.info(f"Ingestion complete for {clean_ticker}. Indexed {new_articles_count} new articles. Rolling sentiment: {stock.rolling_sentiment} ({stock.sentiment_label})")

            return {
                "ticker": clean_ticker,
                "name": stock.name,
                "current_price_inr": stock.current_price_inr,
                "pe_ratio": stock.pe_ratio,
                "debt_to_equity": stock.debt_to_equity,
                "dividend_yield_pct": stock.dividend_yield_pct,
                "rolling_sentiment": stock.rolling_sentiment,
                "sentiment_label": stock.sentiment_label,
                "new_articles_indexed": new_articles_count,
                "total_articles": len(recent_articles)
            }

ingestion_pipeline = StockIngestionPipeline()
