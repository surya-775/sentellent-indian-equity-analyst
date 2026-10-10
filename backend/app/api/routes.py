import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Stock, NewsArticle, User, UserPersona, UserFollowedStock, ChatMessage
from app.api.auth import get_current_user
from app.services.ingestion import ingestion_pipeline
from app.agent.graph import equity_agent
from app.agent.persona import persona_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Request / Response Models ---
class FollowStockRequest(BaseModel):
    ticker: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default-session"

class UpdatePersonaRequest(BaseModel):
    risk_tolerance: Optional[str] = None
    investment_style: Optional[str] = None
    max_debt_to_equity: Optional[float] = None
    min_dividend_yield: Optional[float] = None
    learned_rules: Optional[List[str]] = None

# --- Stock Endpoints ---

@router.get("/stocks")
def list_stocks(db: Session = Depends(get_db)):
    """Returns all tracked Indian equities with live fundamentals and sentiment."""
    stocks = db.query(Stock).order_by(Stock.market_cap_crores_inr.desc()).all()
    return [
        {
            "ticker": s.ticker,
            "name": s.name,
            "exchange": s.exchange,
            "current_price_inr": s.current_price_inr,
            "market_cap_crores_inr": s.market_cap_crores_inr,
            "pe_ratio": s.pe_ratio,
            "debt_to_equity": s.debt_to_equity,
            "dividend_yield_pct": s.dividend_yield_pct,
            "roce_pct": s.roce_pct,
            "roe_pct": s.roe_pct,
            "rolling_sentiment": s.rolling_sentiment,
            "sentiment_label": s.sentiment_label,
            "last_ingested_at": s.last_ingested_at
        }
        for s in stocks
    ]

@router.post("/stocks/follow")
def follow_stock(
    payload: FollowStockRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Follows an Indian stock ticker and runs the concurrent-safe ingestion pipeline
    to fetch fundamentals (Screener.in/yfinance) and Indian financial RSS news.
    """
    clean_ticker = payload.ticker.upper().strip()
    if not clean_ticker:
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")

    # Ingest stock data
    ingest_result = ingestion_pipeline.ingest_stock(db, clean_ticker)

    # Link to user followed stocks
    followed = db.query(UserFollowedStock).filter(
        UserFollowedStock.user_id == user.id,
        UserFollowedStock.ticker == clean_ticker
    ).first()

    if not followed:
        followed = UserFollowedStock(user_id=user.id, ticker=clean_ticker)
        db.add(followed)
        db.commit()

    return {
        "message": f"Successfully followed and ingested {clean_ticker}",
        "stock": ingest_result
    }

@router.post("/stocks/{ticker}/refresh")
def refresh_stock(ticker: str, db: Session = Depends(get_db)):
    """Refreshes fundamentals and news for an existing ticker."""
    clean_ticker = ticker.upper().strip()
    result = ingestion_pipeline.ingest_stock(db, clean_ticker, force_refresh=True)
    return {"message": f"Refreshed {clean_ticker}", "stock": result}

@router.get("/stocks/{ticker}/news")
def get_stock_news(ticker: str, db: Session = Depends(get_db)):
    """Returns vector-indexed news articles and sentiment for a ticker."""
    clean_ticker = ticker.upper().strip()
    articles = db.query(NewsArticle).filter(
        NewsArticle.ticker == clean_ticker
    ).order_by(NewsArticle.published_at.desc()).limit(15).all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "published_at": a.published_at,
            "summary": a.summary,
            "sentiment_score": a.sentiment_score,
            "sentiment_impact": a.sentiment_impact,
            "key_events": a.key_events
        }
        for a in articles
    ]

# --- Persona Endpoints ---

@router.get("/persona")
def get_user_persona(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Returns the user's dynamic investor persona and learned rules."""
    persona = persona_manager.get_or_create_persona(db, user.id)
    return {
        "risk_tolerance": persona.risk_tolerance,
        "investment_style": persona.investment_style,
        "max_debt_to_equity": persona.max_debt_to_equity,
        "min_dividend_yield": persona.min_dividend_yield,
        "preferred_sectors": persona.preferred_sectors,
        "excluded_sectors": persona.excluded_sectors,
        "learned_rules": persona.learned_rules,
        "updated_at": persona.updated_at
    }

@router.post("/persona")
def update_user_persona(
    payload: UpdatePersonaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Manually updates or fine-tunes investor persona parameters."""
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    persona = persona_manager.update_persona(db, user.id, updates)
    return {
        "message": "Persona updated successfully",
        "persona": {
            "risk_tolerance": persona.risk_tolerance,
            "investment_style": persona.investment_style,
            "max_debt_to_equity": persona.max_debt_to_equity,
            "min_dividend_yield": persona.min_dividend_yield,
            "learned_rules": persona.learned_rules
        }
    }

# --- Chat & Agent Endpoints ---

@router.post("/chat")
def chat_with_agent(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Submits user query to the LangGraph Agentic Brain.
    Learns persona from conversation, retrieves grounded news + fundamentals,
    enforces anti-hallucination guardrail, and returns cited responses in INR.
    """
    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty query")

    try:
        # Save user message
        db.add(ChatMessage(
            session_id=payload.session_id,
            user_id=user.id,
            role="user",
            content=user_msg
        ))
        db.commit()

        # Run LangGraph Agent
        result = equity_agent.run(db, user_id=user.id, query=user_msg, session_id=payload.session_id)

        # Save assistant message with citations
        db.add(ChatMessage(
            session_id=payload.session_id,
            user_id=user.id,
            role="assistant",
            content=result["response"],
            citations=result["citations"]
        ))
        db.commit()

        return {
            "reply": result["response"],
            "citations": result["citations"],
            "intent": result["intent"],
            "ticker": result["ticker"]
        }
    except Exception as e:
        logger.exception(f"Error during agent chat execution: {e}")
        db.rollback()
        # Grounded fallback lookup for stock queries
        ticker = equity_agent._extract_ticker(user_msg)
        if ticker:
            fund = agent_tools.get_stock_fundamentals(db, ticker)
            if fund:
                reply = (
                    f"Grounded Indian Equity Analysis: {ticker}\n\n"
                    f"Fundamentals (NSE/BSE & Screener.in):\n"
                    f"- Current Quote: {fund['current_price_inr']}\n"
                    f"- Market Capitalization: {fund['market_cap_inr']}\n"
                    f"- Valuation (P/E): {fund['pe_ratio']} | Debt-to-Equity: {fund['debt_to_equity']}\n"
                    f"- Dividend Yield: {fund['dividend_yield_pct']} | ROCE: {fund['roce_pct']} | ROE: {fund['roe_pct']}\n"
                    f"- Rolling News Sentiment: {fund['sentiment_label']} (Score: {fund['rolling_sentiment']})\n"
                )
                return {
                    "reply": reply,
                    "citations": [{
                        "title": f"{ticker} Consolidated Fundamentals",
                        "url": f"https://www.screener.in/company/{ticker}/",
                        "source": "Screener.in & NSE",
                        "type": "fundamentals"
                    }],
                    "intent": "stock_query",
                    "ticker": ticker
                }
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}")

@router.get("/chat/history")
def get_chat_history(
    session_id: str = "default-session",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Returns chronological conversation history for the session."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id,
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "created_at": m.created_at
        }
        for m in messages
    ]

# --- Health Check ---

@router.get("/health")
def health_check():
    """Health check endpoint for ALB and ECS task monitoring."""
    return {"status": "healthy", "service": "Indian Equity Analyst API", "version": "1.0.0"}
