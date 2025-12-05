"""Customer information collection tool for the AI Receptionist agent."""
from typing import Optional


def collect_customer_info(
    current_info: dict,
    fields_needed: list[str],
    reason: str,
    provided_value: Optional[str] = None,
    provided_field: Optional[str] = None
) -> dict:
    """
    Manage customer information collection.
    
    Args:
        current_info: Current customer info dict from session
        fields_needed: List of fields needed (first_name, last_name, email, phone)
        reason: Why we need this info
        provided_value: If customer provided a value in their message
        provided_field: Which field the provided value corresponds to
        
    Returns:
        {
            "collected_fields": {...},
            "missing_fields": [...],
            "prompt": "..." if fields are missing
        }
    """
    valid_fields = {"first_name", "last_name", "email", "phone"}
    requested_fields = [f for f in fields_needed if f in valid_fields]
    
    collected = dict(current_info)
    
    if provided_value and provided_field and provided_field in valid_fields:
        collected[provided_field] = provided_value
    
    missing = [f for f in requested_fields if not collected.get(f)]
    
    result = {
        "collected_fields": collected,
        "missing_fields": missing,
        "reason": reason,
        "all_collected": len(missing) == 0
    }
    
    if missing:
        field_prompts = {
            "first_name": "your first name",
            "last_name": "your last name",
            "email": "your email address",
            "phone": "your phone number"
        }
        
        if len(missing) == 1:
            result["prompt"] = f"To {reason}, could you please provide {field_prompts.get(missing[0], missing[0])}?"
        else:
            fields_str = ", ".join([field_prompts.get(f, f) for f in missing[:-1]])
            fields_str += f" and {field_prompts.get(missing[-1], missing[-1])}"
            result["prompt"] = f"To {reason}, could you please provide {fields_str}?"
    
    return result


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[-1]


def validate_phone(phone: str) -> bool:
    """Basic phone validation - at least 10 digits."""
    digits = "".join(c for c in phone if c.isdigit())
    return len(digits) >= 10


def parse_customer_input(message: str, expected_field: str) -> dict:
    """
    Parse customer input and try to extract the expected field.
    
    Args:
        message: The customer's message
        expected_field: The field we're expecting (first_name, last_name, email, phone)
        
    Returns:
        {"field": field_name, "value": extracted_value, "valid": bool}
    """
    message = message.strip()
    
    if expected_field == "email":
        words = message.split()
        for word in words:
            if "@" in word and validate_email(word):
                return {"field": "email", "value": word, "valid": True}
        if "@" in message and validate_email(message):
            return {"field": "email", "value": message, "valid": True}
        return {"field": "email", "value": message, "valid": False, "error": "Invalid email format"}
    
    elif expected_field == "phone":
        digits = "".join(c for c in message if c.isdigit())
        if validate_phone(message):
            return {"field": "phone", "value": message, "valid": True}
        return {"field": "phone", "value": message, "valid": False, "error": "Please provide a valid phone number"}
    
    elif expected_field in ["first_name", "last_name"]:
        name = message.split()[0] if message.split() else message
        if name and name.replace("-", "").replace("'", "").isalpha():
            return {"field": expected_field, "value": name.title(), "valid": True}
        return {"field": expected_field, "value": message, "valid": len(message) > 0}
    
    return {"field": expected_field, "value": message, "valid": True}
