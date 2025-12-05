"""Pydantic models for the API."""
from .business import Business, BusinessCreate, BusinessUpdate, BusinessConfig
from .user import User, UserCreate, UserLogin
from .service import Service, ServiceCreate
from .staff import Staff, StaffCreate
from .conversation import Conversation, ChatMessage, ChatRequest, ChatResponse

# V2 Models
from .appointment import (
    Appointment, AppointmentCreate, AppointmentUpdate,
    TimeSlot, AvailabilityResponse, BookingConfirmation
)
from .lead import (
    Lead, LeadCreate, LeadUpdate,
    WaitlistEntry, WaitlistCreate, WaitlistUpdate, WaitlistPosition
)
from .customer import (
    Customer, CustomerCreate, CustomerUpdate,
    CustomerIdentification, CustomerHistory, CustomerVisit
)
from .campaign import (
    Campaign, CampaignCreate, CampaignUpdate,
    RecipientFilter, CampaignSendResult
)

__all__ = [
    # V1 Models
    "Business", "BusinessCreate", "BusinessUpdate", "BusinessConfig",
    "User", "UserCreate", "UserLogin",
    "Service", "ServiceCreate",
    "Staff", "StaffCreate",
    "Conversation", "ChatMessage", "ChatRequest", "ChatResponse",
    # V2 Models
    "Appointment", "AppointmentCreate", "AppointmentUpdate",
    "TimeSlot", "AvailabilityResponse", "BookingConfirmation",
    "Lead", "LeadCreate", "LeadUpdate",
    "WaitlistEntry", "WaitlistCreate", "WaitlistUpdate", "WaitlistPosition",
    "Customer", "CustomerCreate", "CustomerUpdate",
    "CustomerIdentification", "CustomerHistory", "CustomerVisit",
    "Campaign", "CampaignCreate", "CampaignUpdate",
    "RecipientFilter", "CampaignSendResult",
]
