import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Stock, NewsArticle, UserPersona
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class AgentTools:
    def __init__(self):
        self.vector_store = vector_store_service

    def get_stock_fundamentals(self, db: Session, ticker: str) -> Optional[Dict[str, Any]]:
        clean_ticker = ticker.upper().strip()
        stock = db.query(Stock).filter(Stock.ticker == clean_ticker).first()
        if not stock:
            return None

        return {
            "ticker": stock.ticker,
            "name": stock.name,
            "exchange": stock.exchange,
            "current_price_inr": f"₹{stock.current_price_inr:,.2f}",
            "market_cap_inr": f"₹{stock.market_cap_crores_inr:,.0f} Cr",
            "pe_ratio": stock.pe_ratio,
            "debt_to_equity": stock.debt_to_equity,
            "dividend_yield_pct": f"{stock.dividend_yield_pct}%" if stock.dividend_yield_pct is not None else "N/A",
            "roce_pct": f"{stock.roce_pct}%" if stock.roce_pct is not None else "N/A",
            "roe_pct": f"{stock.roe_pct}%" if stock.roe_pct is not None else "N/A",
            "rolling_sentiment": stock.rolling_sentiment,
            "sentiment_label": stock.sentiment_label,
            "last_ingested_at": stock.last_ingested_at.strftime("%Y-%m-%d %H:%M UTC") if stock.last_ingested_at else "N/A",
            "citation": f"NSE/BSE & Screener.in Fundamentals Row for {stock.ticker}"
        }

    def get_stock_news(self, db: Session, ticker: str, query: str = "", top_k: int = 4) -> List[Dict[str, Any]]:
        clean_ticker = ticker.upper().strip()
        search_query = query if query else f"{clean_ticker} news sentiment earnings"
        return self.vector_store.search_articles(db, search_query, ticker=clean_ticker, top_k=top_k)

    def screen_and_rank_stocks(self, db: Session, persona: UserPersona) -> List[Dict[str, Any]]:
        """
        Algorithmic screening and multi-factor scoring against investor persona.
        Applies hard rules (e.g. screen out high debt), evaluates growth/value/stability/momentum/quality,
        and returns grounded picks with 1-line reasons.
        """
        all_stocks = db.query(Stock).all()
        if not all_stocks:
            return []

        qualified_picks = []
        max_de = persona.max_debt_to_equity or 1.5
        min_div = persona.min_dividend_yield or 0.0
        excluded = [s.lower() for s in (persona.excluded_sectors or [])]

        for s in all_stocks:
            # 1. Hard Rule Filtering
            # Screen out high debt if user rule specifies
            if s.debt_to_equity is not None and s.debt_to_equity > max_de:
                logger.info(f"Screened out {s.ticker} due to high debt: {s.debt_to_equity} > {max_de}")
                continue

            # Screen out excluded sectors
            if s.sector and any(exc in s.sector.lower() for exc in excluded):
                logger.info(f"Screened out {s.ticker} due to excluded sector: {s.sector}")
                continue

            # Screen out if below min dividend threshold
            if min_div > 0 and (s.dividend_yield_pct or 0.0) < min_div:
                logger.info(f"Screened out {s.ticker} due to low dividend yield: {s.dividend_yield_pct} < {min_div}")
                continue

            # 2. Multi-Factor Scoring (Growth, Value, Stability, Momentum, Quality)
            # Factor 1: Stability (Low debt + healthy ROE)
            de_score = max(0.0, 1.0 - (s.debt_to_equity or 0.5))
            roe_score = min(1.0, (s.roe_pct or 12.0) / 30.0)
            stability = (de_score + roe_score) / 2.0

            # Factor 2: Value (Reasonable P/E)
            pe = s.pe_ratio or 25.0
            value = max(0.0, min(1.0, 40.0 / (pe + 5.0)))

            # Factor 3: Momentum / Sentiment
            sentiment_norm = (s.rolling_sentiment + 1.0) / 2.0 # convert -1..1 to 0..1

            # Factor 4: Quality & Dividend
            div_score = min(1.0, (s.dividend_yield_pct or 0.0) / 3.0)
            quality = min(1.0, (s.roce_pct or 15.0) / 30.0)

            # Weightings tailored to persona style
            if "dividend" in persona.investment_style.lower() or "conservative" in persona.risk_tolerance.lower():
                total_score = (div_score * 0.35) + (stability * 0.35) + (quality * 0.15) + (sentiment_norm * 0.15)
                reason = f"High dividend yield ({s.dividend_yield_pct}%), conservative balance sheet (D/E: {s.debt_to_equity}), and resilient ROCE ({s.roce_pct}%)."
            elif "value" in persona.investment_style.lower():
                total_score = (value * 0.4) + (stability * 0.3) + (sentiment_norm * 0.2) + (quality * 0.1)
                reason = f"Attractive valuation at P/E of {s.pe_ratio} with manageable debt ratio of {s.debt_to_equity}."
            else: # Growth / Balanced
                total_score = (quality * 0.3) + (sentiment_norm * 0.3) + (stability * 0.2) + (value * 0.2)
                reason = f"Solid operational momentum with {s.sentiment_label} sentiment ({s.rolling_sentiment}) and strong return on equity ({s.roe_pct}%)."

            # Fetch a top recent article for citation
            recent_art = db.query(NewsArticle).filter(NewsArticle.ticker == s.ticker).order_by(NewsArticle.published_at.desc()).first()

            qualified_picks.append({
                "ticker": s.ticker,
                "name": s.name,
                "current_price_inr": f"₹{s.current_price_inr:,.2f}",
                "market_cap_inr": f"₹{s.market_cap_crores_inr:,.0f} Cr",
                "pe_ratio": s.pe_ratio,
                "debt_to_equity": s.debt_to_equity,
                "dividend_yield_pct": s.dividend_yield_pct,
                "sentiment_label": s.sentiment_label,
                "score": round(total_score * 100, 1),
                "reason": reason,
                "citation": {
                    "source": recent_art.source if recent_art else "NSE/BSE Corporate Filings",
                    "title": recent_art.title if recent_art else f"{s.ticker} Annual Financials & Ratios",
                    "url": recent_art.url if recent_art else f"https://www.screener.in/company/{s.ticker}/"
                }
            })

        qualified_picks.sort(key=lambda x: x["score"], reverse=True)
        return qualified_picks

agent_tools = AgentTools()
