import re
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END
from app.config import settings
from app.db.models import Stock, NewsArticle, UserPersona
from app.agent.persona import persona_manager
from app.agent.tools import agent_tools
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    user_id: int
    session_id: str
    intent: str
    ticker_mentioned: Optional[str]
    persona_updates: Dict[str, Any]
    retrieved_fundamentals: Optional[Dict[str, Any]]
    retrieved_articles: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    response_text: str
    citations: List[Dict[str, Any]]
    has_data: bool

class IndianEquityAgentGraph:
    def __init__(self):
        self.tools = agent_tools
        self.persona_mgr = persona_manager
        self.vector_store = vector_store_service
        self.workflow = self._build_graph()

    def _extract_ticker(self, query: str) -> Optional[str]:
        # 1. Regex patterns for queries like "sentiment on TCS", "about RELIANCE", "quote of INFY"
        match = re.search(r"(?:sentiment on|about|for|quote of|performance of|analyze)\s+([A-Za-z0-9_]{2,15})", query, re.IGNORECASE)
        if match:
            candidate = match.group(1).upper().strip()
            if candidate not in ["THIS", "NEXT", "THE", "MY", "YOUR", "INDIAN", "MARKET", "STOCKS"]:
                return candidate

        known = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "TATAMOTORS"]
        words = re.findall(r"\b[A-Za-z0-9&_]+\b", query)
        for w in words:
            if w.upper() in known:
                return w.upper()

        # Check by company name keyword
        q_low = query.lower()
        if "reliance" in q_low or "ril" in q_low:
            return "RELIANCE"
        if "tcs" in q_low or "tata consultancy" in q_low:
            return "TCS"
        if "hdfc" in q_low:
            return "HDFCBANK"
        if "infosys" in q_low or "infy" in q_low:
            return "INFY"
        if "sbi" in q_low or "state bank" in q_low:
            return "SBIN"
        if "airtel" in q_low:
            return "BHARTIARTL"
        if "itc" in q_low:
            return "ITC"
        if "l&t" in q_low or "larsen" in q_low:
            return "LT"

        # Check for uppercase ticker tokens that are not standard English stopwords
        stopwords = {"WHAT", "IS", "THE", "ON", "THIS", "WEEK", "BUY", "SELL", "HOW", "WHY", "ARE", "FOR", "AND", "NOT", "YES", "YOU", "ALL", "WHO"}
        for w in words:
            if w.isupper() and len(w) >= 3 and w not in stopwords:
                return w

        return None


    def route_intent_node(self, state: AgentState) -> AgentState:
        query = state["query"]
        q_low = query.lower()
        
        # Check persona statements
        persona_updates = self.persona_mgr.extract_persona_updates_from_text(query)
        ticker = self._extract_ticker(query)
        
        state["ticker_mentioned"] = ticker
        state["persona_updates"] = persona_updates

        if persona_updates and ("i'm" in q_low or "i am" in q_low or "avoid" in q_low or "prefer" in q_low):
            state["intent"] = "persona_update"
        elif any(k in q_low for k in ["recommend", "what should i buy", "picks", "portfolio", "what to buy"]):
            state["intent"] = "recommendation"
        elif ticker:
            state["intent"] = "stock_query"
        else:
            state["intent"] = "general_query"

        return state

    def update_persona_node(self, state: AgentState, db: Session) -> AgentState:
        if state["persona_updates"]:
            updated = self.persona_mgr.update_persona(db, state["user_id"], state["persona_updates"])
            logger.info(f"Updated persona for user {state['user_id']}: {updated.learned_rules}")
        return state

    def retrieve_node(self, state: AgentState, db: Session) -> AgentState:
        ticker = state["ticker_mentioned"]
        if ticker:
            fundamentals = self.tools.get_stock_fundamentals(db, ticker)
            news = self.tools.get_stock_news(db, ticker, query=state["query"])
            state["retrieved_fundamentals"] = fundamentals
            state["retrieved_articles"] = news
            state["has_data"] = bool(fundamentals or news)
        elif state["intent"] == "recommendation":
            persona = self.persona_mgr.get_or_create_persona(db, state["user_id"])
            recommendations = self.tools.screen_and_rank_stocks(db, persona)
            state["recommendations"] = recommendations
            state["has_data"] = bool(recommendations)
        else:
            state["has_data"] = True
        return state

    def anti_hallucination_node(self, state: AgentState) -> AgentState:
        """
        Anti-Hallucination Guardrail:
        If a claim/query isn't supported by ingested data, the agent explicitly says so.
        """
        if state["intent"] == "stock_query" and not state["has_data"]:
            ticker = state.get("ticker_mentioned", "the specified stock")
            state["response_text"] = (
                f"I don't have that in the ingested data. '{ticker}' has not been ingested yet. "
                f"Please follow or ingest {ticker} using the Watchlist to fetch its Screener fundamentals and recent Indian financial news."
            )
            state["citations"] = []
        return state

    def synthesize_response_node(self, state: AgentState, db: Session) -> AgentState:
        if state.get("response_text"): # Already set by anti-hallucination guard
            return state

        intent = state["intent"]
        user_id = state["user_id"]
        persona = self.persona_mgr.get_or_create_persona(db, user_id)
        citations = []

        if intent == "persona_update":
            rules_str = ", ".join(persona.learned_rules) if persona.learned_rules else "Standard parameters"
            state["response_text"] = (
                f"Understood. I have updated your investor profile and memory:\n\n"
                f"- Risk Tolerance: {persona.risk_tolerance}\n"
                f"- Investment Style: {persona.investment_style}\n"
                f"- Max Debt-to-Equity: {persona.max_debt_to_equity}\n"
                f"- Min Dividend Yield: {persona.min_dividend_yield}%\n"
                f"- Active Rules: {rules_str}\n\n"
                f"Your memory graph and persona vector have been updated. Any future recommendations or screening queries will screen out non-compliant stocks accordingly."
            )
            state["citations"] = []

        elif intent == "recommendation":
            recs = state.get("recommendations", [])
            if not recs:
                state["response_text"] = (
                    "I don't have sufficient ingested data matching your profile criteria. "
                    "All currently ingested stocks either exceed your debt limit or lack recent data. "
                    "Please ingest more NSE/BSE tickers into your watchlist."
                )
            else:
                lines = [
                    f"Personalised Indian Equity Recommendations for Your Profile:\n",
                    f"Persona Applied: {persona.risk_tolerance} Risk | {persona.investment_style} Style | Max D/E: {persona.max_debt_to_equity} | Min Div: {persona.min_dividend_yield}%\n"
                ]
                for idx, r in enumerate(recs[:4], start=1):
                    lines.append(
                        f"{idx}. {r['ticker']} ({r['name']})\n"
                        f"- Current Price: {r['current_price_inr']} | Market Cap: {r['market_cap_inr']}\n"
                        f"- Ratios: P/E: {r['pe_ratio']} | Debt-to-Equity: {r['debt_to_equity']} | Dividend Yield: {r['dividend_yield_pct']}%\n"
                        f"- Rolling Sentiment: {r['sentiment_label']}\n"
                        f"- Rationale: {r['reason']}\n"
                        f"- Source Citation: [{r['citation']['title']}]({r['citation']['url']}) ({r['citation']['source']})\n"
                    )
                    citations.append({
                        "title": r['citation']['title'],
                        "url": r['citation']['url'],
                        "source": r['citation']['source'],
                        "type": "Recommendation & Fundamentals"
                    })
                state["response_text"] = "\n".join(lines)
                state["citations"] = citations

        elif intent == "stock_query":
            fund = state.get("retrieved_fundamentals")
            news = state.get("retrieved_articles", [])
            ticker = state.get("ticker_mentioned", "")

            lines = [f"Grounded Indian Equity Analysis: {ticker}\n"]
            if fund:
                lines.append(
                    f"Fundamentals (NSE/BSE & Screener.in):\n"
                    f"- Current Quote: {fund['current_price_inr']}\n"
                    f"- Market Capitalization: {fund['market_cap_inr']}\n"
                    f"- Valuation (P/E): {fund['pe_ratio']} | Debt-to-Equity: {fund['debt_to_equity']}\n"
                    f"- Dividend Yield: {fund['dividend_yield_pct']} | ROCE: {fund['roce_pct']} | ROE: {fund['roe_pct']}\n"
                    f"- Rolling News Sentiment: {fund['sentiment_label']} (Score: {fund['rolling_sentiment']})\n"
                )
                citations.append({
                    "title": f"{ticker} Consolidated Fundamentals",
                    "url": f"https://www.screener.in/company/{ticker}/",
                    "source": "Screener.in & NSE",
                    "type": "fundamentals"
                })

            if news:
                lines.append(f"Recent Grounded News & Market Developments:")
                for n in news[:3]:
                    lines.append(
                        f"- {n['title']}\n"
                        f"  Source: {n['source']} | Sentiment Impact: {n['sentiment_impact']} (Score: {n['sentiment_score']})\n"
                        f"  Summary: {n['summary']}\n"
                        f"  Citation Link: [{n['title']}]({n['url']})\n"
                    )
                    citations.append({
                        "title": n['title'],
                        "url": n['url'],
                        "source": n['source'],
                        "type": "news"
                    })

            state["response_text"] = "\n".join(lines)
            state["citations"] = citations

        else: # general_query
            state["response_text"] = (
                "Welcome to your Personal Agentic AI Indian-Equity Analyst. You can:\n\n"
                "1. Follow/Ingest Tickers: Add NSE/BSE stocks like RELIANCE, TCS, HDFCBANK, or INFY to fetch fundamentals & Indian financial news.\n"
                "2. Ask Grounded Stock Questions: e.g., 'What's the sentiment on TCS this week?' or 'Show me Reliance's debt and dividend metrics'.\n"
                "3. Train Your Persona: e.g., 'I'm a conservative, dividend-focused investor and I avoid high-debt companies'.\n"
                "4. Get Cited Recommendations: e.g., 'What should I buy this week?' (screened against your persona with citations in INR).\n\n"
                "What stock or strategy would you like to explore today?"
            )
            state["citations"] = []


        return state

    def _build_graph(self):
        graph = StateGraph(AgentState)
        
        # Node wrappers for graph execution
        graph.add_node("route_intent", self.route_intent_node)
        graph.add_node("anti_hallucination_check", self.anti_hallucination_node)
        
        graph.set_entry_point("route_intent")
        graph.add_edge("route_intent", "anti_hallucination_check")
        graph.add_edge("anti_hallucination_check", END)
        
        return graph.compile()

    def run(self, db: Session, user_id: int, query: str, session_id: str = "default") -> Dict[str, Any]:
        """Runs the LangGraph agent pipeline."""
        initial_state: AgentState = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "intent": "",
            "ticker_mentioned": None,
            "persona_updates": {},
            "retrieved_fundamentals": None,
            "retrieved_articles": [],
            "recommendations": [],
            "response_text": "",
            "citations": [],
            "has_data": True
        }

        # 1. Route Intent & Extract Persona
        state = self.route_intent_node(initial_state)

        # 2. Update Dynamic Persona Memory
        state = self.update_persona_node(state, db)

        # 3. Grounded Retrieval (Vector + SQL)
        state = self.retrieve_node(state, db)

        # 4. Anti-Hallucination Guardrail
        state = self.anti_hallucination_node(state)

        # 5. Synthesize Grounded, Cited Response in INR
        state = self.synthesize_response_node(state, db)

        return {
            "response": state["response_text"],
            "citations": state["citations"],
            "intent": state["intent"],
            "ticker": state["ticker_mentioned"]
        }

equity_agent = IndianEquityAgentGraph()
