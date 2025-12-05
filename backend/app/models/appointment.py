"""Appointment models for V2."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


AppointmentStatus = Literal['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']


class AppointmentBase(BaseModel):
    """Base appointment fields."""
    service_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM format
    duration_minutes: int
    staff_id: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Create appointment request."""
    customer_id: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Update appointment request."""
    service_id: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration_minutes: Optional[int] = None
    staff_id: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class Appointment(AppointmentBase):
    """Full appointment model."""
    id: str
    business_id: str
    customer_id: Optional[str] = None
    status: AppointmentStatus = 'scheduled'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Joined fields for display
    service_name: Optional[str] = None
    staff_name: Optional[str] = None


class TimeSlot(BaseModel):
    """Available time slot."""
    id: str
    date: str
    time: str
    staff_id: Optional[str] = None
    staff_name: Optional[str] = None
    duration_minutes: int


class AvailabilityResponse(BaseModel):
    """Response for availability check."""
    slots: list[TimeSlot] = Field(default_factory=list)
    service_id: str
    service_name: Optional[str] = None
    date_range: str
    calendar_ui_data: Optional[dict] = None


class BookingConfirmation(BaseModel):
    """Booking confirmation response."""
    confirmation_id: str
    service: str
    date: str
    time: str
    duration_minutes: int
    staff_name: Optional[str] = None
    customer_name: str
    message: str
