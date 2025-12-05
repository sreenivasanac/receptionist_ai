"""Modular prompts for the receptionist agent."""
from .base import get_base_prompt
from .booking_flow import get_booking_flow_rules
from .customer import get_customer_rules
from .ui_rules import get_ui_display_rules
from .verticals import get_vertical_context, GREETING_MESSAGES


def get_system_prompt(business_name: str, business_type: str) -> str:
    """
    Generate the full system prompt for the receptionist agent.
    
    Args:
        business_name: Name of the business
        business_type: Type/vertical (beauty, wellness, medical, fitness)
        
    Returns:
        Complete system prompt
    """
    return "\n\n".join([
        get_base_prompt(business_name, business_type),
        get_booking_flow_rules(),
        get_customer_rules(),
        get_ui_display_rules(),
        get_vertical_context(business_type),
    ])


def get_greeting_message(business_name: str, business_type: str) -> str:
    """Get the appropriate greeting message for the business."""
    template = GREETING_MESSAGES.get(
        business_type.lower(),
        GREETING_MESSAGES["wellness"]
    )
    return template.format(business_name=business_name)


__all__ = [
    "get_system_prompt",
    "get_greeting_message",
]
