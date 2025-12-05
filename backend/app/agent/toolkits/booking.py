"""Booking toolkit - availability, booking, cancel, reschedule."""
from typing import Optional

from agno.tools import Toolkit

from app.tools.booking import (
    check_availability as booking_check_availability,
    book_appointment as booking_book_appointment,
    cancel_appointment as booking_cancel_appointment,
    reschedule_appointment as booking_reschedule_appointment,
)


class BookingToolkit(Toolkit):
    """Toolkit for appointment booking operations."""
    
    def __init__(self, business_id: str, config: dict, **kwargs):
        self.business_id = business_id
        self.config = config
        # State for tracking booking flow
        self.selected_service_id: Optional[str] = None
        self.selected_slot_id: Optional[str] = None
        self.pending_reschedule_appointment: Optional[dict] = None
        # UI state
        self.pending_input_type: Optional[str] = None
        self.pending_input_config: Optional[dict] = None
        
        tools = [
            self.start_booking_flow,
            self.check_availability,
            self.book_appointment,
            self.cancel_appointment,
            self.reschedule_appointment,
        ]
        super().__init__(name="booking_tools", tools=tools, **kwargs)
    
    def start_booking_flow(self, services_list: list[dict]) -> str:
        """
        Start the appointment booking process.
        Call this when a customer wants to book an appointment.
        
        Args:
            services_list: List of available services from BusinessInfoToolkit
        """
        self.pending_input_type = "service_select"
        self.pending_input_config = {
            "services": services_list,
            "multi_select": False
        }
        return "Great! Please select a service from the options below:"
    
    def check_availability(
        self,
        service_id: Optional[str] = None,
        date_range: str = "this week",
        time_preference: Optional[str] = None,
        staff_id: Optional[str] = None
    ) -> str:
        """
        Check available appointment slots for a service.
        
        Args:
            service_id: ID of the service (optional - uses previously selected)
            date_range: When to look for slots (e.g., 'this week', 'tomorrow')
            time_preference: Preferred time (e.g., 'morning', 'afternoon')
            staff_id: Optional specific staff member ID
        """
        if not self.business_id:
            return "Booking is not available at this time."
        
        actual_service_id = service_id or self.selected_service_id
        if not actual_service_id:
            return "Please select a service first before checking availability."
        
        result = booking_check_availability(
            business_id=self.business_id,
            service_id=actual_service_id,
            date_range=date_range,
            time_preference=time_preference,
            staff_id=staff_id,
            config=self.config
        )
        
        if 'error' in result:
            return result['error']
        
        slots = result.get('slots', [])
        if not slots:
            return f"I'm sorry, there are no available slots for {result.get('service_name', 'this service')} during {date_range}. Would you like to try a different time or be added to our waitlist?"
        
        self.selected_service_id = actual_service_id
        
        # Set up calendar UI
        self.pending_input_type = "datetime_picker"
        self.pending_input_config = {
            "min_date": result['calendar_ui_data'].get('min_date'),
            "max_date": result['calendar_ui_data'].get('max_date'),
            "available_dates": result['calendar_ui_data'].get('available_dates', []),
            "time_slots": result['calendar_ui_data'].get('time_slots', []),
            "slots": slots
        }
        
        service_name = result.get('service_name', 'your appointment')
        return f"I found {len(slots)} available time slots for {service_name}. Please select your preferred date and time from the calendar below."
    
    def book_appointment(
        self,
        customer_name: str,
        customer_phone: str,
        slot_id: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> str:
        """
        Book a confirmed appointment.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            slot_id: The slot ID (optional - uses tracked selection)
            customer_email: Customer's email (optional)
        """
        if not self.business_id or not self.selected_service_id:
            return "Please select a service and time first."
        
        actual_slot_id = slot_id or self.selected_slot_id
        if not actual_slot_id:
            return "Please select a time slot first before booking."
        
        result = booking_book_appointment(
            business_id=self.business_id,
            service_id=self.selected_service_id,
            slot_id=actual_slot_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            config=self.config
        )
        
        if 'error' in result:
            return result['error']
        
        # Clear booking state
        self.selected_service_id = None
        self.selected_slot_id = None
        
        return result['message'] + f"\n\nConfirmation #: {result['confirmation_id'][:8].upper()}"
    
    def cancel_appointment(
        self,
        customer_phone: str,
        appointment_id: Optional[str] = None
    ) -> str:
        """
        Cancel an existing appointment.
        
        Args:
            customer_phone: Customer's phone number
            appointment_id: Optional specific appointment ID
        """
        if not self.business_id:
            return "Cancellation is not available at this time."
        
        result = booking_cancel_appointment(
            business_id=self.business_id,
            customer_phone=customer_phone,
            appointment_id=appointment_id
        )
        
        return result['message']
    
    def reschedule_appointment(
        self,
        appointment_id: Optional[str] = None,
        new_slot_id: Optional[str] = None
    ) -> str:
        """
        Reschedule an existing appointment to a new time.
        
        Args:
            appointment_id: The appointment ID (optional - uses tracked)
            new_slot_id: New time slot ID (optional - uses tracked)
        """
        if not self.business_id:
            return "Rescheduling is not available at this time."
        
        actual_appointment_id = appointment_id
        if not actual_appointment_id and self.pending_reschedule_appointment:
            actual_appointment_id = self.pending_reschedule_appointment.get('appointment_id')
        
        if not actual_appointment_id:
            return "No appointment found to reschedule."
        
        actual_slot_id = new_slot_id or self.selected_slot_id
        if not actual_slot_id:
            return "Please select a new time slot from the calendar first."
        
        result = booking_reschedule_appointment(
            business_id=self.business_id,
            appointment_id=actual_appointment_id,
            new_slot_id=actual_slot_id
        )
        
        if 'error' in result:
            return result['error']
        
        # Clear state
        self.pending_reschedule_appointment = None
        self.selected_slot_id = None
        self.selected_service_id = None
        
        return result['message']
    
    def clear_pending_ui(self):
        """Clear any pending UI state."""
        self.pending_input_type = None
        self.pending_input_config = None
