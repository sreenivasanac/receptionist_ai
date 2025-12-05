"""YAML configuration parsing and validation."""
from typing import Optional
import yaml

from app.models.business import BusinessConfig, BusinessHours, ServiceConfig, PolicyConfig, FAQConfig


def parse_config_yaml(yaml_content: str) -> Optional[BusinessConfig]:
    """
    Parse and validate YAML configuration.
    
    Args:
        yaml_content: Raw YAML string
        
    Returns:
        Parsed BusinessConfig or None if invalid
    """
    if not yaml_content:
        return None
    
    try:
        data = yaml.safe_load(yaml_content)
        if not data:
            return None
        
        hours = {}
        for day, h in data.get("hours", {}).items():
            if isinstance(h, dict):
                hours[day] = BusinessHours(
                    open=h.get("open"),
                    close=h.get("close"),
                    closed=h.get("closed", False)
                )
        
        services = []
        for s in data.get("services", []):
            if isinstance(s, dict):
                services.append(ServiceConfig(
                    id=s.get("id", ""),
                    name=s.get("name", ""),
                    duration_minutes=s.get("duration_minutes", 30),
                    price=s.get("price", 0),
                    description=s.get("description", "")
                ))
        
        policies_data = data.get("policies", {})
        policies = PolicyConfig(
            cancellation=policies_data.get("cancellation", ""),
            deposit=policies_data.get("deposit", False),
            deposit_amount=policies_data.get("deposit_amount", 0),
            walk_ins=policies_data.get("walk_ins", "")
        )
        
        faqs = []
        for f in data.get("faqs", []):
            if isinstance(f, dict):
                faqs.append(FAQConfig(
                    question=f.get("question", ""),
                    answer=f.get("answer", "")
                ))
        
        return BusinessConfig(
            business_id=data.get("business_id", ""),
            name=data.get("name", ""),
            location=data.get("location", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            hours=hours,
            services=services,
            policies=policies,
            faqs=faqs
        )
        
    except yaml.YAMLError:
        return None
    except Exception:
        return None


def config_to_yaml(config: BusinessConfig) -> str:
    """
    Convert BusinessConfig to YAML string.
    
    Args:
        config: BusinessConfig object
        
    Returns:
        YAML string
    """
    data = {
        "business_id": config.business_id,
        "name": config.name,
        "location": config.location,
        "phone": config.phone,
        "email": config.email,
        "hours": {},
        "services": [],
        "policies": {},
        "faqs": []
    }
    
    for day, h in config.hours.items():
        if h.closed:
            data["hours"][day] = {"closed": True}
        else:
            data["hours"][day] = {"open": h.open, "close": h.close}
    
    for s in config.services:
        data["services"].append({
            "id": s.id,
            "name": s.name,
            "duration_minutes": s.duration_minutes,
            "price": s.price,
            "description": s.description
        })
    
    data["policies"] = {
        "cancellation": config.policies.cancellation,
        "deposit": config.policies.deposit,
        "deposit_amount": config.policies.deposit_amount,
        "walk_ins": config.policies.walk_ins
    }
    
    for f in config.faqs:
        data["faqs"].append({
            "question": f.question,
            "answer": f.answer
        })
    
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


def merge_scraped_with_config(existing_config: dict, scraped_info: dict) -> dict:
    """
    Merge scraped website info into existing config.
    Only fills in missing fields, doesn't overwrite.
    
    Args:
        existing_config: Current business configuration
        scraped_info: Parsed scraped data
        
    Returns:
        Merged configuration dict
    """
    merged = dict(existing_config)
    
    if not merged.get("phone") and scraped_info.get("phone"):
        merged["phone"] = scraped_info["phone"]
    
    if not merged.get("email") and scraped_info.get("email"):
        merged["email"] = scraped_info["email"]
    
    if not merged.get("location") and scraped_info.get("location"):
        merged["location"] = scraped_info["location"]
    
    return merged
