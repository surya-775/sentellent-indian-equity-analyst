import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, User, Stock, NewsArticle
from app.agent.persona import PersonaManager
from app.agent.tools import AgentTools
from app.agent.graph import IndianEquityAgentGraph

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Create test user
    user = User(id=1, email="harisankar@sentellent.com", name="Test Evaluator")
    db.add(user)
    
    # Add high-debt stock and low-debt stock
    high_debt = Stock(
        ticker="HIGHDEBT",
        name="High Debt Corp Ltd",
        current_price_inr=150.0,
        debt_to_equity=1.8, # High debt
        dividend_yield_pct=0.5,
        pe_ratio=22.0,
        rolling_sentiment=0.1,
        sentiment_label="Neutral"
    )
    low_debt_div = Stock(
        ticker="LOWDEBT",
        name="Low Debt Dividend Stars Ltd",
        current_price_inr=3200.0,
        debt_to_equity=0.1, # Low debt
        dividend_yield_pct=3.2, # Strong dividend
        pe_ratio=18.0,
        rolling_sentiment=0.5,
        sentiment_label="Bullish"
    )
    db.add_all([high_debt, low_debt_div])
    db.commit()
    
    yield db
    db.close()

def test_persona_rule_extraction():
    mgr = PersonaManager()
    prompt = "I'm a conservative, dividend-focused investor and I avoid high-debt companies"
    updates = mgr.extract_persona_updates_from_text(prompt)

    assert updates["risk_tolerance"] == "Conservative"
    assert updates["investment_style"] == "Dividend & Income"
    assert updates["max_debt_to_equity"] == 0.5
    assert len(updates["learned_rules"]) >= 2

def test_persona_screening_out_high_debt(test_db):
    mgr = PersonaManager()
    tools = AgentTools()

    # Update persona with strict debt rule
    mgr.update_persona(test_db, user_id=1, updates={
        "risk_tolerance": "Conservative",
        "investment_style": "Dividend & Income",
        "max_debt_to_equity": 0.5,
        "min_dividend_yield": 1.0
    })
    persona = mgr.get_or_create_persona(test_db, user_id=1)

    # Screen and rank
    picks = tools.screen_and_rank_stocks(test_db, persona)
    pick_tickers = [p["ticker"] for p in picks]

    # HIGHDEBT must be screened out!
    assert "HIGHDEBT" not in pick_tickers
    assert "LOWDEBT" in pick_tickers

def test_anti_hallucination_on_unknown_stock(test_db):
    agent = IndianEquityAgentGraph()
    # Querying a stock not in the database
    res = agent.run(test_db, user_id=1, query="What is the sentiment on UNKNOWN_TICKER_XYZ this week?")
    assert "I don't have that in the ingested data" in res["response"]
