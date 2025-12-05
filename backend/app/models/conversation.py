"""Conversation and chat models."""
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class CustomerInfo(BaseModel):
    """Customer information collected during chat."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ServiceOption(BaseModel):
    """Service option for selection."""
    id: str
    name: str
    price: float
    duration_minutes: Optional[int] = None
    description: Optional[str] = None


class TimeSlotOption(BaseModel):
    """Available time slot for booking."""
    id: str
    date: str
    time: str
    staff_id: Optional[str] = None
    staff_name: Optional[str] = None
    duration_minutes: Optional[int] = None


class InputConfig(BaseModel):
    """Configuration for structured input components."""
    # Service selection
    services: Optional[list[ServiceOption]] = None
    multi_select: bool = False
    # Contact form
    fields: Optional[list[str]] = None
    # Date/time picker
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    available_dates: Optional[list[str]] = None
    time_slots: Optional[list[str]] = None
    slots: Optional[list[TimeSlotOption]] = None  # Full slot objects for V2 booking


class ChatRequest(BaseModel):
    """Chat request from widget."""
    business_id: str
    session_id: str
    message: str
    customer_info: Optional[CustomerInfo] = None


class ChatResponse(BaseModel):
    """Chat response to widget."""
    session_id: str
    message: str
    input_type: str = "text"  # text, service_select, datetime_picker, contact_form
    input_config: Optional[InputConfig] = None
    customer_info_needed: list[str] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)


class Conversation(BaseModel):
    """Conversation session."""
    id: str
    business_id: str
    session_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    customer_info: CustomerInfo = Field(default_factory=CustomerInfo)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
