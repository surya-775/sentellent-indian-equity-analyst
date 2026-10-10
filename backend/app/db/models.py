import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.database import Base, engine

from sqlalchemy.types import TypeDecorator

class VectorType(TypeDecorator):
    """Seamless vector storage supporting pgvector on PostgreSQL and JSON text on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(1536))
            except ImportError:
                return dialect.type_descriptor(Text)
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except Exception:
                return value
        return value


class Stock(Base):
    __tablename__ = "stocks"

    ticker = Column(String(20), primary_key=True, index=True) # e.g. RELIANCE, TCS
    name = Column(String(255), nullable=False)
    exchange = Column(String(10), default="NSE") # NSE / BSE
    nse_id = Column(String(50), nullable=True)
    bse_id = Column(String(50), nullable=True)
    sector = Column(String(100), default="Diversified")
    
    # Fundamentals in INR
    current_price_inr = Column(Float, default=0.0)
    market_cap_crores_inr = Column(Float, default=0.0)
    pe_ratio = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    dividend_yield_pct = Column(Float, nullable=True)
    roce_pct = Column(Float, nullable=True)
    roe_pct = Column(Float, nullable=True)
    profit_growth_qoq_pct = Column(Float, nullable=True)
    
    # Sentiment & Metadata
    rolling_sentiment = Column(Float, default=0.0) # -1.0 to +1.0
    sentiment_label = Column(String(20), default="Neutral")
    last_ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    articles = relationship("NewsArticle", back_populates="stock")
    followers = relationship("UserFollowedStock", back_populates="stock")

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_hash = Column(String(64), unique=True, index=True, nullable=False) # SHA-256 for dedup
    ticker = Column(String(20), ForeignKey("stocks.ticker"), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(100), nullable=False) # Economic Times, Moneycontrol, Mint, etc.
    published_at = Column(DateTime, default=datetime.datetime.utcnow)
    summary = Column(Text, nullable=True)
    content_snippet = Column(Text, nullable=True)
    
    # Enrichment
    sentiment_score = Column(Float, default=0.0) # -1.0 to +1.0
    sentiment_impact = Column(String(50), default="Neutral")
    key_events = Column(JSON, default=list) # e.g. ["Rising debt", "Capex announcement"]
    
    # Embedding vector
    embedding = Column(VectorType, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    stock = relationship("Stock", back_populates="articles")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    persona = relationship("UserPersona", back_populates="user", uselist=False)
    followed_stocks = relationship("UserFollowedStock", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")

class UserPersona(Base):
    __tablename__ = "user_personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    risk_tolerance = Column(String(50), default="Moderate") # Conservative, Moderate, Aggressive
    investment_style = Column(String(50), default="Growth & Value") # Dividend, Growth, Value
    max_debt_to_equity = Column(Float, default=1.0) # Screen out stocks higher than this
    min_dividend_yield = Column(Float, default=0.0)
    preferred_sectors = Column(JSON, default=list)
    excluded_sectors = Column(JSON, default=list)
    learned_rules = Column(JSON, default=list) # e.g. ["avoid high-debt companies", "prefers PSU dividends"]
    
    persona_embedding = Column(VectorType, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="persona")

class UserFollowedStock(Base):
    __tablename__ = "user_followed_stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), ForeignKey("stocks.ticker"), nullable=False)
    followed_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "ticker", name="_user_ticker_uc"),)

    user = relationship("User", back_populates="followed_stocks")
    stock = relationship("Stock", back_populates="followers")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(20), nullable=False) # user / assistant / system
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=list) # [{ "title": "...", "url": "...", "snippet": "...", "type": "news"|"fundamentals" }]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")
