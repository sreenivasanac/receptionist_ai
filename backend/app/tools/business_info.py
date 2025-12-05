"""Business information tools for the AI Receptionist agent."""
import json
from typing import Optional
import yaml


def get_business_hours(config: dict, day: Optional[str] = None) -> dict:
    """
    Get business hours for a specific day or all days.
    
    Args:
        config: The business configuration dict
        day: Optional specific day (monday, tuesday, etc.) or None for all days
        
    Returns:
        Hours information for the requested day(s)
    """
    hours = config.get("hours", {})
    
    if day:
        day_lower = day.lower()
        if day_lower in hours:
            day_hours = hours[day_lower]
            if day_hours.get("closed", False):
                return {"day": day_lower, "status": "closed"}
            return {
                "day": day_lower,
                "open": day_hours.get("open", ""),
                "close": day_hours.get("close", ""),
                "status": "open"
            }
        return {"day": day_lower, "error": "Day not found"}
    
    result = {"hours": {}}
    for d, h in hours.items():
        if h.get("closed", False):
            result["hours"][d] = {"status": "closed"}
        else:
            result["hours"][d] = {
                "open": h.get("open", ""),
                "close": h.get("close", ""),
                "status": "open"
            }
    return result


def get_service_details(config: dict, service_id: Optional[str] = None, service_name: Optional[str] = None) -> dict:
    """
    Get details for a specific service or all services.
    
    Args:
        config: The business configuration dict
        service_id: Optional service ID to filter
        service_name: Optional service name to search (partial match)
        
    Returns:
        Service details
    """
    services = config.get("services", [])
    
    if service_id:
        for service in services:
            if service.get("id") == service_id:
                return {"service": service}
        return {"error": f"Service with ID '{service_id}' not found"}
    
    if service_name:
        name_lower = service_name.lower()
        matching = [s for s in services if name_lower in s.get("name", "").lower()]
        if matching:
            return {"services": matching, "count": len(matching)}
        return {"error": f"No services matching '{service_name}' found", "services": []}
    
    return {"services": services, "count": len(services)}


def get_policies(config: dict, policy_type: Optional[str] = None) -> dict:
    """
    Get business policies.
    
    Args:
        config: The business configuration dict
        policy_type: Optional specific policy (cancellation, deposit, walk_ins)
        
    Returns:
        Policy information
    """
    policies = config.get("policies", {})
    
    if policy_type:
        type_lower = policy_type.lower().replace(" ", "_").replace("-", "_")
        if type_lower in policies:
            return {"policy": type_lower, "value": policies[type_lower]}
        return {"error": f"Policy '{policy_type}' not found"}
    
    return {"policies": policies}


def search_faqs(config: dict, query: str) -> dict:
    """
    Search through FAQs for relevant answers.
    
    Args:
        config: The business configuration dict
        query: The search query
        
    Returns:
        Matching FAQs
    """
    faqs = config.get("faqs", [])
    query_lower = query.lower()
    
    query_words = set(query_lower.split())
    
    scored_faqs = []
    for faq in faqs:
        question_lower = faq.get("question", "").lower()
        answer_lower = faq.get("answer", "").lower()
        
        score = 0
        for word in query_words:
            if len(word) > 2:
                if word in question_lower:
                    score += 2
                if word in answer_lower:
                    score += 1
        
        if score > 0:
            scored_faqs.append({"faq": faq, "score": score})
    
    scored_faqs.sort(key=lambda x: x["score"], reverse=True)
    
    if scored_faqs:
        return {
            "matches": [sf["faq"] for sf in scored_faqs[:3]],
            "count": len(scored_faqs)
        }
    
    return {"matches": [], "count": 0, "message": "No matching FAQs found"}


def get_business_info(config: dict, query_type: str, specific_item: Optional[str] = None) -> dict:
    """
    Main business info retrieval tool - delegates to specific functions.
    
    Args:
        config: The business configuration dict
        query_type: Type of info (hours, services, pricing, location, policies, faqs)
        specific_item: Optional specific item to query
        
    Returns:
        Requested business information
    """
    query_type_lower = query_type.lower()
    
    if query_type_lower == "hours":
        return get_business_hours(config, specific_item)
    
    elif query_type_lower in ["services", "pricing"]:
        return get_service_details(config, service_name=specific_item)
    
    elif query_type_lower == "location":
        return {
            "name": config.get("name", ""),
            "location": config.get("location", ""),
            "phone": config.get("phone", ""),
            "email": config.get("email", "")
        }
    
    elif query_type_lower == "policies":
        return get_policies(config, specific_item)
    
    elif query_type_lower == "faqs":
        if specific_item:
            return search_faqs(config, specific_item)
        return {"faqs": config.get("faqs", [])}
    
    return {"error": f"Unknown query type: {query_type}"}
