"""Agent tools for the AI Receptionist."""
# V1 Tools
from .business_info import get_business_hours, get_service_details, get_policies, search_faqs
from .customer_info import collect_customer_info

# V2 Tools
from .booking import (
    check_availability,
    book_appointment,
    cancel_appointment,
    reschedule_appointment
)
from .leads import (
    capture_lead,
    add_to_waitlist,
    get_lead,
    update_lead_status
)
from .customers import (
    identify_customer,
    get_customer_history,
    create_or_update_customer,
    get_rebooking_suggestion
)

# V3 Tools
from .recommendations import recommend_service
from .workflows import (
    check_workflow_triggers,
    execute_workflow,
    execute_triggered_workflows
)

__all__ = [
    # V1 Tools
    "get_business_hours",
    "get_service_details", 
    "get_policies",
    "search_faqs",
    "collect_customer_info",
    # V2 Tools - Booking
    "check_availability",
    "book_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    # V2 Tools - Leads
    "capture_lead",
    "add_to_waitlist",
    "get_lead",
    "update_lead_status",
    # V2 Tools - Customers
    "identify_customer",
    "get_customer_history",
    "create_or_update_customer",
    "get_rebooking_suggestion",
    # V3 Tools
    "recommend_service",
    "check_workflow_triggers",
    "execute_workflow",
    "execute_triggered_workflows",
]
