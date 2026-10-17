# server/app/services/ai_service.py
from typing import Optional, Dict, Any

class AIService:
    """
    Optional add-on service for intent analysis and content generation.
    Decoupled from core deterministic Trigger -> Condition -> Action automation engine.
    """
    @staticmethod
    async def classify_comment_intent(comment_text: str) -> Dict[str, Any]:
        """
        Optional intent classification (e.g. Lead, Support, Spam, Positive).
        Fallback returns basic rule-based match if AI provider is unconfigured.
        """
        lower = comment_text.lower()
        if any(w in lower for w in ["price", "cost", "how much", "$"]):
            return {"intent": "PRICE_INQUIRY", "confidence": 0.95}
        elif any(w in lower for w in ["link", "guide", "pdf", "send", "dm"]):
            return {"intent": "RESOURCE_REQUEST", "confidence": 0.98}
        elif any(w in lower for w in ["scam", "fake", "bad", "hate"]):
            return {"intent": "NEGATIVE_SENTIMENT", "confidence": 0.85}
        return {"intent": "GENERAL_ENGAGEMENT", "confidence": 0.70}

    @staticmethod
    async def generate_contextual_dm(lead_name: str, keyword: str, resource_url: str) -> str:
        """
        Generates a friendly personalized DM copy.
        """
        return f"Hey {lead_name}! Thanks for checking out our post. Here is the link you requested for {keyword}: {resource_url}"
