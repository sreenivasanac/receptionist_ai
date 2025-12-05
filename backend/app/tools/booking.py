"""Booking tools for V2 - appointment scheduling."""
from typing import Optional
from app.services.calendar import (
    check_availability as calendar_check_availability,
    book_appointment as calendar_book_appointment,
    cancel_appointment as calendar_cancel_appointment,
    reschedule_appointment as calendar_reschedule_appointment
)


def check_availability(
    business_id: str,
    service_id: str,
    date_range: str,
    time_preference: Optional[str] = None,
    staff_id: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Check available appointment slots.
    
    Args:
        business_id: Business ID
        service_id: ID of the service to book
        date_range: e.g., "this week", "tomorrow", "Dec 15-20"
        time_preference: e.g., "morning", "after 5pm", "afternoon"
        staff_id: Optional specific staff member
        config: Business config for hours
    
    Returns:
        {
            "slots": [{"id", "date", "time", "staff_name", "duration"}],
            "service_name": "...",
            "calendar_ui_data": {...}
        }
    """
    return calendar_check_availability(
        business_id=business_id,
        service_id=service_id,
        date_range=date_range,
        time_preference=time_preference,
        staff_id=staff_id,
        config=config
    )


def book_appointment(
    business_id: str,
    service_id: str,
    slot_id: str,
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str] = None,
    customer_id: Optional[str] = None,
    notes: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Book a confirmed appointment.
    
    Args:
        business_id: Business ID
        service_id: Service to book
        slot_id: Selected slot ID from check_availability
        customer_name: Customer's full name
        customer_phone: Customer phone number
        customer_email: Customer email (optional)
        customer_id: Customer ID if returning (optional)
        notes: Appointment notes (optional)
        config: Business config (optional)
    
    Returns:
        {"confirmation_id", "service", "date", "time", "staff", "message"}
    """
    return calendar_book_appointment(
        business_id=business_id,
        service_id=service_id,
        slot_id=slot_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_id=customer_id,
        notes=notes,
        config=config
    )


def cancel_appointment(
    business_id: str,
    customer_phone: str,
    appointment_id: Optional[str] = None
) -> dict:
    """
    Cancel an existing appointment.
    
    Args:
        business_id: Business ID
        customer_phone: Customer phone number to find appointment
        appointment_id: Optional specific appointment ID
    
    Returns:
        {"cancelled": bool, "message"}
    """
    return calendar_cancel_appointment(
        business_id=business_id,
        customer_phone=customer_phone,
        appointment_id=appointment_id
    )


def reschedule_appointment(
    business_id: str,
    appointment_id: str,
    new_slot_id: str
) -> dict:
    """
    Reschedule to a new time slot.
    
    Args:
        business_id: Business ID  
        appointment_id: Current appointment ID
        new_slot_id: New slot ID from check_availability
    
    Returns:
        {"new_confirmation_id", "new_date", "new_time", "message"}
    """
    return calendar_reschedule_appointment(
        business_id=business_id,
        appointment_id=appointment_id,
        new_slot_id=new_slot_id
    )
