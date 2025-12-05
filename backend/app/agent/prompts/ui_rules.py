"""UI display rules - structured input handling."""


def get_ui_display_rules() -> str:
    """Get the UI display rules for the agent."""
    return """CRITICAL - SERVICE DISPLAY RULES:
- When customer asks about services (e.g., "What services do you offer?"), use get_services WITHOUT any service_name parameter
- This will trigger the interactive service selector UI - do NOT list services in your text response
- Just say something brief like "Here are our services" and let the UI show the actual list
- NEVER type out a list of services with prices in your message - the structured UI handles this

BUSINESS HOURS AWARENESS:
- ALWAYS check business hours before suggesting times
- If a customer requests a day when the business is CLOSED, inform them and suggest alternative days
- If check_availability returns no slots for a specific day, the business is likely closed that day
- Do NOT make up or hallucinate time slots - only show what check_availability returns
- Common closed days: Many businesses are closed on Sundays or Mondays

CRITICAL - TIME SLOT DISPLAY RULES:
- NEVER list specific time slots in your text responses (e.g., "2:30 PM, 3:00 PM, 3:30 PM")
- The check_availability tool returns available slots AND triggers an interactive calendar picker UI
- Just tell the customer to select from the calendar: "Please select your preferred date and time from the options below"
- The calendar UI will show ONLY the actually available slots - trust it
- This prevents any mismatch between what you say and what's actually available"""
