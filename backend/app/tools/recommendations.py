"""Service recommendation tool for V3."""
from typing import Optional
import re


def recommend_service(
    business_id: str,
    goals: str,
    concerns: Optional[str] = None,
    preferences: Optional[str] = None,
    budget: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Recommend services based on customer goals, concerns, and preferences.
    Uses keyword matching against service names and descriptions.
    
    Args:
        business_id: Business ID
        goals: Customer's goals (e.g., "look refreshed", "relax", "lose weight")
        concerns: Specific concerns (e.g., "wrinkles", "back pain", "acne")
        preferences: Preferences (e.g., "quick", "non-invasive", "natural")
        budget: Budget indication (e.g., "under $100", "premium")
        config: Business configuration with services
    
    Returns:
        {
            "recommendations": [
                {"service_id", "name", "price", "duration_minutes", "reason", "match_score"}
            ],
            "message": "Based on your goals..."
        }
    """
    if not config:
        return {
            "recommendations": [],
            "message": "Unable to provide recommendations at this time."
        }
    
    services = config.get("services", [])
    if not services:
        return {
            "recommendations": [],
            "message": "No services available to recommend."
        }
    
    search_text = f"{goals} {concerns or ''} {preferences or ''}".lower()
    
    scored_services = []
    for service in services:
        score = _calculate_match_score(service, search_text, budget)
        if score > 0:
            reason = _generate_reason(service, goals, concerns, preferences)
            scored_services.append({
                "service_id": service.get("id", service.get("name", "").lower().replace(" ", "_")),
                "name": service.get("name", ""),
                "price": service.get("price", 0),
                "duration_minutes": service.get("duration_minutes"),
                "description": service.get("description", ""),
                "reason": reason,
                "match_score": score
            })
    
    scored_services.sort(key=lambda x: x["match_score"], reverse=True)
    top_recommendations = scored_services[:3]
    
    if not top_recommendations:
        return {
            "recommendations": [],
            "message": f"I couldn't find a perfect match for '{goals}', but I'd be happy to help you explore our services. What specific results are you hoping to achieve?"
        }
    
    if len(top_recommendations) == 1:
        rec = top_recommendations[0]
        message = f"Based on your goals, I'd recommend our **{rec['name']}** (${rec['price']}). {rec['reason']}"
    else:
        message = f"Based on what you've shared, here are my top recommendations:\n\n"
        for i, rec in enumerate(top_recommendations, 1):
            message += f"{i}. **{rec['name']}** - ${rec['price']}\n   {rec['reason']}\n\n"
        message += "Would you like more details on any of these, or shall I help you book?"
    
    return {
        "recommendations": top_recommendations,
        "message": message
    }


def _calculate_match_score(service: dict, search_text: str, budget: Optional[str]) -> int:
    """Calculate how well a service matches the search criteria."""
    score = 0
    
    service_name = service.get("name", "").lower()
    service_desc = service.get("description", "").lower()
    service_text = f"{service_name} {service_desc}"
    
    keywords = GOAL_KEYWORDS.copy()
    keywords.update(CONCERN_KEYWORDS)
    keywords.update(PREFERENCE_KEYWORDS)
    
    for keyword, related_terms in keywords.items():
        if keyword in search_text:
            for term in related_terms:
                if term in service_text:
                    score += 10
                    break
    
    search_words = set(re.findall(r'\b\w+\b', search_text))
    service_words = set(re.findall(r'\b\w+\b', service_text))
    common_words = search_words & service_words - STOP_WORDS
    score += len(common_words) * 5
    
    if budget:
        price = service.get("price", 0)
        budget_lower = budget.lower()
        
        if "under" in budget_lower or "less than" in budget_lower:
            try:
                budget_amount = int(re.search(r'\d+', budget_lower).group())
                if price <= budget_amount:
                    score += 15
                else:
                    score -= 20
            except:
                pass
        elif "premium" in budget_lower or "high-end" in budget_lower:
            if price > 150:
                score += 10
        elif "budget" in budget_lower or "affordable" in budget_lower:
            if price < 75:
                score += 10
    
    return max(0, score)


def _generate_reason(
    service: dict,
    goals: str,
    concerns: Optional[str],
    preferences: Optional[str]
) -> str:
    """Generate a personalized reason for recommending this service."""
    name = service.get("name", "This service")
    desc = service.get("description", "")
    
    reasons = []
    
    goals_lower = goals.lower()
    if any(word in goals_lower for word in ["relax", "stress", "tension", "unwind"]):
        reasons.append("perfect for relaxation and stress relief")
    elif any(word in goals_lower for word in ["refresh", "rejuvenate", "younger", "youthful"]):
        reasons.append("great for a refreshed, youthful appearance")
    elif any(word in goals_lower for word in ["pain", "sore", "ache", "tight"]):
        reasons.append("excellent for relieving pain and discomfort")
    elif any(word in goals_lower for word in ["weight", "fit", "tone", "slim"]):
        reasons.append("effective for your fitness goals")
    elif any(word in goals_lower for word in ["skin", "glow", "clear", "acne"]):
        reasons.append("wonderful for improving skin health")
    
    if concerns:
        concerns_lower = concerns.lower()
        if any(word in concerns_lower for word in ["wrinkle", "lines", "aging"]):
            reasons.append("targets fine lines and wrinkles")
        elif any(word in concerns_lower for word in ["acne", "breakout", "pore"]):
            reasons.append("helps with acne and skin clarity")
        elif any(word in concerns_lower for word in ["back", "neck", "shoulder"]):
            reasons.append("focuses on problem areas")
    
    if preferences:
        pref_lower = preferences.lower()
        if "quick" in pref_lower or "fast" in pref_lower:
            duration = service.get("duration_minutes", 60)
            if duration and duration <= 45:
                reasons.append(f"can be completed in just {duration} minutes")
        elif "natural" in pref_lower:
            reasons.append("uses natural, gentle approaches")
    
    if reasons:
        return reasons[0].capitalize() + "."
    elif desc:
        return desc[:100] + ("..." if len(desc) > 100 else "")
    else:
        return "A popular choice among our clients."


GOAL_KEYWORDS = {
    "relax": ["massage", "spa", "relaxation", "stress", "calm", "soothing"],
    "refresh": ["facial", "rejuvenate", "glow", "revitalize", "hydrating"],
    "younger": ["anti-aging", "botox", "filler", "lift", "wrinkle", "collagen"],
    "pain": ["massage", "therapy", "deep tissue", "relief", "chiropractic"],
    "weight": ["weight loss", "body", "sculpt", "tone", "slimming", "contour"],
    "skin": ["facial", "peel", "treatment", "skincare", "dermabrasion"],
    "hair": ["haircut", "color", "style", "treatment", "keratin", "highlights"],
    "nails": ["manicure", "pedicure", "nail", "gel", "polish"],
    "fitness": ["training", "class", "workout", "exercise", "gym"],
    "wellness": ["holistic", "wellness", "healing", "balance", "energy"],
}

CONCERN_KEYWORDS = {
    "wrinkle": ["botox", "filler", "anti-aging", "lift", "collagen"],
    "acne": ["facial", "peel", "treatment", "clear", "extraction"],
    "back": ["massage", "deep tissue", "therapy", "spine"],
    "stress": ["massage", "relaxation", "spa", "meditation", "calm"],
    "dry": ["hydrating", "moisturizing", "treatment", "facial"],
    "oily": ["balancing", "mattifying", "pore", "treatment"],
}

PREFERENCE_KEYWORDS = {
    "quick": ["express", "mini", "30", "quick"],
    "natural": ["organic", "natural", "holistic", "gentle"],
    "luxury": ["premium", "deluxe", "signature", "vip"],
    "gentle": ["sensitive", "gentle", "light", "soothing"],
}

STOP_WORDS = {
    "i", "me", "my", "want", "need", "looking", "for", "to", "a", "an",
    "the", "and", "or", "but", "in", "on", "at", "with", "that", "this",
    "is", "are", "was", "be", "have", "has", "do", "does", "would", "like",
    "some", "something", "anything", "get", "make", "feel", "look"
}
