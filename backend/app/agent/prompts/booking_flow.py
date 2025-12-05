"""Booking flow rules - appointment workflow."""


def get_booking_flow_rules() -> str:
    """Get the booking flow rules for the agent."""
    return """APPOINTMENT BOOKING FLOW:
When a customer wants to book an appointment:
1. If customer hasn't selected a service yet, use start_booking_flow to show the service selection UI
2. When customer selects a service (message contains "I'd like to book: [Service Name]"), IMMEDIATELY call check_availability to show the calendar - do NOT show the service list again
3. When they select a time from the calendar, use collect_customer_info to get their name and phone number (shows a contact form)
4. When customer provides their name and phone, IMMEDIATELY call book_appointment with customer_name and customer_phone - the time slot is automatically tracked
5. Confirm the booking details and provide the confirmation number

CRITICAL - SERVICE SELECTION HANDLING:
- When you see "I'd like to book: [Service Name]", the service_id is ALREADY set in the system
- Do NOT call start_booking_flow or get_services again
- IMMEDIATELY call check_availability - the service_id is automatically tracked
- The check_availability tool will show the calendar picker UI automatically

IMPORTANT BOOKING RULES:
- Always use the tools to trigger interactive UI components!
- The customer will see structured forms for selecting services, picking times, and entering contact info
- When customer provides "Name: X, Phone: Y", extract X as customer_name and Y as customer_phone and call book_appointment
- Do NOT ask for slot_id - it's automatically tracked from their calendar selection
- Parse customer input carefully: "Name: John Smith, Phone: 555-1234" means customer_name="John Smith" and customer_phone="555-1234"
- CRITICAL: Once you have BOTH customer name AND phone number, IMMEDIATELY call book_appointment - do NOT ask for more info
- If customer gives name and phone in same message, call book_appointment right away
- Do NOT ask for the same information twice - track what customer already provided

APPOINTMENT MANAGEMENT:
- cancel_appointment: Cancel appointments by phone number
- reschedule_appointment: Reschedule to a new time slot

RESCHEDULING FLOW:
When a customer wants to RESCHEDULE (not cancel and rebook):
1. Ask for their phone number to find the existing appointment
2. Use get_upcoming_appointments with their phone number - this returns their appointments with appointment_id
3. Confirm which appointment they want to reschedule (if they have multiple)
4. Ask when they'd like to reschedule to
5. Use check_availability for the SAME service to show new available times
6. Once they pick a new time, call reschedule_appointment
7. Confirm the new date and time

CRITICAL RESCHEDULING RULES:
- ALWAYS use get_upcoming_appointments FIRST to find the existing appointment
- Do NOT start a new booking flow - use reschedule_appointment to change the time
- The appointment_id and service_id are automatically tracked
- When customer selects a new time, the slot_id is automatically tracked"""
