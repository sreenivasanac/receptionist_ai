"""Lead and waitlist models for V2."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


LeadStatus = Literal['new', 'contacted', 'qualified', 'converted', 'lost']
WaitlistStatus = Literal['waiting', 'notified', 'booked', 'expired', 'cancelled']
ContactMethod = Literal['phone', 'email', 'sms']


class LeadBase(BaseModel):
    """Base lead fields."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    interest: str
    notes: Optional[str] = None
    company: Optional[str] = None


class LeadCreate(LeadBase):
    """Create lead request."""
    source: str = 'chatbot'


class LeadUpdate(BaseModel):
    """Update lead request."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    interest: Optional[str] = None
    notes: Optional[str] = None
    company: Optional[str] = None
    status: Optional[LeadStatus] = None


class Lead(LeadBase):
    """Full lead model."""
    id: str
    business_id: str
    status: LeadStatus = 'new'
    source: str = 'chatbot'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WaitlistBase(BaseModel):
    """Base waitlist fields."""
    service_id: str
    customer_name: str
    customer_contact: str
    preferred_dates: list[str] = Field(default_factory=list)
    preferred_times: list[str] = Field(default_factory=list)
    contact_method: ContactMethod = 'phone'
    notes: Optional[str] = None


class WaitlistCreate(WaitlistBase):
    """Create waitlist entry request."""
    customer_id: Optional[str] = None


class WaitlistUpdate(BaseModel):
    """Update waitlist entry request."""
    preferred_dates: Optional[list[str]] = None
    preferred_times: Optional[list[str]] = None
    contact_method: Optional[ContactMethod] = None
    status: Optional[WaitlistStatus] = None
    notes: Optional[str] = None


class WaitlistEntry(WaitlistBase):
    """Full waitlist entry model."""
    id: str
    business_id: str
    customer_id: Optional[str] = None
    status: WaitlistStatus = 'waiting'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Joined fields for display
    service_name: Optional[str] = None


class WaitlistPosition(BaseModel):
    """Waitlist position response."""
    waitlist_id: str
    position: int
    service_name: str
    message: str
