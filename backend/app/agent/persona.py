import json
import logging
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import User, UserPersona
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class PersonaManager:
    def __init__(self):
        self.vector_store = vector_store_service

    def get_or_create_persona(self, db: Session, user_id: int) -> UserPersona:
        persona = db.query(UserPersona).filter(UserPersona.user_id == user_id).first()
        if not persona:
            default_persona_text = "Moderate risk investor seeking balanced growth and quality Indian equities"
            vec = self.vector_store.embed_text(default_persona_text)
            persona = UserPersona(
                user_id=user_id,
                risk_tolerance="Moderate",
                investment_style="Growth & Value",
                max_debt_to_equity=1.0,
                min_dividend_yield=0.5,
                preferred_sectors=["IT", "Banking", "FMCG"],
                excluded_sectors=[],
                learned_rules=["Balanced risk and growth"],
                persona_embedding=json.dumps(vec) if not ("postgresql" in str(db.bind.url)) else vec
            )
            db.add(persona)
            db.commit()
            db.refresh(persona)
        return persona

    def extract_persona_updates_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extracts investor persona rules and constraints from conversational text.
        e.g., "I'm a conservative, dividend-focused investor and I avoid high-debt companies"
        """
        text_lower = text.lower()
        updates: Dict[str, Any] = {}
        new_rules: List[str] = []

        # Risk tolerance detection
        if "conservative" in text_lower or "low risk" in text_lower or "capital preservation" in text_lower:
            updates["risk_tolerance"] = "Conservative"
            new_rules.append("Conservative capital-preservation approach")
        elif "aggressive" in text_lower or "high risk" in text_lower or "high reward" in text_lower:
            updates["risk_tolerance"] = "Aggressive"
            new_rules.append("Aggressive growth orientation")
        elif "moderate" in text_lower:
            updates["risk_tolerance"] = "Moderate"

        # Investment style
        if "dividend" in text_lower:
            updates["investment_style"] = "Dividend & Income"
            updates["min_dividend_yield"] = 1.5
            new_rules.append("Focus on regular dividend yield (>1.5%)")
        if "value" in text_lower or "undervalued" in text_lower or "low pe" in text_lower:
            updates["investment_style"] = "Value Investing"
            new_rules.append("Preference for low P/E value bargains")
        if "growth" in text_lower or "fast growing" in text_lower:
            updates["investment_style"] = "High Growth"

        # Debt constraints
        if "avoid high-debt" in text_lower or "avoid debt" in text_lower or "low debt" in text_lower or "debt free" in text_lower:
            updates["max_debt_to_equity"] = 0.5
            new_rules.append("Strict rule: Screen out high-debt companies (Debt-to-Equity > 0.5)")

        # Sector rules
        if "avoid it" in text_lower or "no it" in text_lower or "exclude tech" in text_lower:
            updates["excluded_sectors"] = ["Information Technology"]
            new_rules.append("Avoid Information Technology sector")

        if new_rules:
            updates["learned_rules"] = new_rules

        return updates

    def update_persona(self, db: Session, user_id: int, updates: Dict[str, Any]) -> UserPersona:
        persona = self.get_or_create_persona(db, user_id)
        
        if "risk_tolerance" in updates:
            persona.risk_tolerance = updates["risk_tolerance"]
        if "investment_style" in updates:
            persona.investment_style = updates["investment_style"]
        if "max_debt_to_equity" in updates:
            persona.max_debt_to_equity = updates["max_debt_to_equity"]
        if "min_dividend_yield" in updates:
            persona.min_dividend_yield = updates["min_dividend_yield"]
        if "excluded_sectors" in updates:
            current_excluded = set(persona.excluded_sectors or [])
            current_excluded.update(updates["excluded_sectors"])
            persona.excluded_sectors = list(current_excluded)
        if "learned_rules" in updates:
            current_rules = list(persona.learned_rules or [])
            for r in updates["learned_rules"]:
                if r not in current_rules:
                    current_rules.append(r)
            persona.learned_rules = current_rules

        # Update persona vector embedding
        summary_text = (
            f"Risk: {persona.risk_tolerance}. Style: {persona.investment_style}. "
            f"Max D/E: {persona.max_debt_to_equity}. Min Div: {persona.min_dividend_yield}%. "
            f"Rules: {', '.join(persona.learned_rules or [])}"
        )
        vec = self.vector_store.embed_text(summary_text)
        persona.persona_embedding = json.dumps(vec) if not ("postgresql" in str(db.bind.url)) else vec

        db.commit()
        db.refresh(persona)
        return persona

persona_manager = PersonaManager()
