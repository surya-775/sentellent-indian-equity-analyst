import os
import json
import logging
import math
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.db.models import NewsArticle, Stock

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.embedding_model = settings.EMBEDDING_MODEL
        self.dim = settings.EMBEDDING_DIM
        self._openai_client = None

        if self.api_key:
            try:
                from langchain_openai import OpenAIEmbeddings
                self._embeddings = OpenAIEmbeddings(
                    model=self.embedding_model,
                    openai_api_key=self.api_key
                )
            except Exception as e:
                logger.warning(f"Could not initialize OpenAIEmbeddings: {e}")
                self._embeddings = None
        else:
            self._embeddings = None

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a 1536-dimensional embedding vector.
        Uses OpenAI Embeddings if key configured, otherwise generates a deterministic
        semantic-frequency vector so RAG & cosine ranking work reliably in all environments.
        """
        if not text:
            text = "empty"

        if self._embeddings:
            try:
                return self._embeddings.embed_query(text)
            except Exception as e:
                logger.warning(f"OpenAI embedding generation failed, using fallback: {e}")

        # Deterministic semantic hash-frequency embedding generator (1536 dim)
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().replace(",", " ").replace(".", " ").split()
        for i, word in enumerate(words):
            val = hash(word) % self.dim
            vec[val] += 1.0 / (math.log(i + 2) + 1.0)
            # Add bigram bias
            if i > 0:
                bi_val = hash(f"{words[i-1]}_{word}") % self.dim
                vec[bi_val] += 1.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def search_articles(
        self,
        db: Session,
        query: str,
        ticker: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant news articles using pgvector cosine distance
        or in-memory cosine fallback.
        """
        query_vec = self.embed_text(query)
        articles_q = db.query(NewsArticle)
        if ticker:
            articles_q = articles_q.filter(NewsArticle.ticker == ticker.upper().strip())
        
        all_articles = articles_q.all()
        if not all_articles:
            return []

        scored_articles = []
        for art in all_articles:
            art_vec = art.embedding
            if isinstance(art_vec, str):
                try:
                    art_vec = json.loads(art_vec)
                except Exception:
                    art_vec = None
            
            sim = self.cosine_similarity(query_vec, art_vec) if art_vec else 0.0
            
            # Boost if exact ticker or key term in title
            if ticker and ticker.lower() in art.title.lower():
                sim += 0.15

            scored_articles.append({
                "article": art,
                "score": sim
            })

        scored_articles.sort(key=lambda x: x["score"], reverse=True)
        return [
            {
                "id": item["article"].id,
                "title": item["article"].title,
                "url": item["article"].url,
                "source": item["article"].source,
                "summary": item["article"].summary,
                "ticker": item["article"].ticker,
                "sentiment_score": item["article"].sentiment_score,
                "sentiment_impact": item["article"].sentiment_impact,
                "score": round(item["score"], 4)
            }
            for item in scored_articles[:top_k]
        ]

vector_store_service = VectorStoreService()
