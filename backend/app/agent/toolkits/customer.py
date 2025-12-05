"""Customer toolkit - identify, history, upcoming appointments."""
from typing import Optional

from agno.tools import Toolkit

from app.tools.customers import (
    identify_customer as customers_identify,
    get_customer_history as customers_get_history,
    get_rebooking_suggestion,
    get_upcoming_appointments as customers_get_upcoming,
)
from app.tools.customer_info import collect_customer_info, parse_customer_input


class CustomerToolkit(Toolkit):
    """Toolkit for customer-related operations."""
    
    def __init__(self, business_id: str, **kwargs):
        self.business_id = business_id
        # Customer state
        self.customer_info: dict = {}
        self.current_customer_id: Optional[str] = None
        self.collecting_field: Optional[str] = None
        # UI state
        self.pending_input_type: Optional[str] = None
        self.pending_input_config: Optional[dict] = None
        
        tools = [
            self.identify_customer,
            self.get_upcoming_appointments,
            self.get_customer_history,
            self.suggest_rebooking,
            self.collect_customer_info,
        ]
        super().__init__(name="customer_tools", tools=tools, **kwargs)
    
    def identify_customer(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> str:
        """
        Identify if a customer is new or returning.
        
        Args:
            phone: Customer's phone number
            email: Customer's email address
        """
        if not self.business_id:
            return "Customer identification is not available."
        
        result = customers_identify(
            business_id=self.business_id,
            phone=phone,
            email=email
        )
        
        if result.get('customer_id'):
            self.current_customer_id = result['customer_id']
            self.customer_info['first_name'] = result.get('first_name', result.get('name', '').split()[0])
        
        return result['message']
    
    def get_upcoming_appointments(self, customer_phone: str) -> str:
        """
        Get upcoming appointments for a customer by their phone number.
        
        Args:
            customer_phone: Customer's phone number
        """
        if not self.business_id:
            return "Appointment lookup is not available."
        
        result = customers_get_upcoming(
            business_id=self.business_id,
            customer_phone=customer_phone
        )
        
        appointments = result.get('appointments', [])
        if not appointments:
            return result['message']
        
        # Store first appointment for potential rescheduling (accessible by BookingToolkit)
        self._pending_reschedule_appointment = appointments[0] if appointments else None
        self._selected_service_id = appointments[0]['service_id'] if appointments else None
        
        response = [result['message']]
        if len(appointments) > 1:
            response.append("\nYour upcoming appointments:")
            for appt in appointments:
                line = f"- {appt['service']} on {appt['date']} at {appt['time']}"
                if appt.get('staff_name'):
                    line += f" with {appt['staff_name']}"
                line += f" (ID: {appt['appointment_id'][:8]})"
                response.append(line)
        
        return "\n".join(response)
    
    def get_customer_history(self, customer_id: Optional[str] = None) -> str:
        """
        Get visit history for a returning customer.
        
        Args:
            customer_id: Customer ID (uses current if not provided)
        """
        if not self.business_id:
            return "Customer history is not available."
        
        cust_id = customer_id or self.current_customer_id
        if not cust_id:
            return "No customer identified yet. Please provide a phone number or email first."
        
        result = customers_get_history(
            business_id=self.business_id,
            customer_id=cust_id
        )
        
        if 'error' in result:
            return result['error']
        
        visits = result.get('visits', [])
        if not visits:
            return f"No visit history found for {result.get('name', 'this customer')}."
        
        history = [f"**Visit History for {result['name']}**\n"]
        history.append(f"Total visits: {result['total_visits']}")
        if result.get('favorite_service'):
            history.append(f"Favorite service: {result['favorite_service']}")
        history.append("\nRecent visits:")
        
        for visit in visits[:5]:
            history.append(f"- {visit['date']}: {visit['service']}" + 
                          (f" with {visit['staff_name']}" if visit.get('staff_name') else ""))
        
        return "\n".join(history)
    
    def suggest_rebooking(self) -> str:
        """
        Get a rebooking suggestion for the current returning customer.
        """
        if not self.business_id or not self.current_customer_id:
            return "Please identify the customer first to get rebooking suggestions."
        
        result = get_rebooking_suggestion(
            business_id=self.business_id,
            customer_id=self.current_customer_id
        )
        
        if 'error' in result:
            return result['error']
        
        return result.get('message', "Would you like to book your next appointment?")
    
    def collect_customer_info(self, fields: str, reason: str) -> str:
        """
        Collect customer information for booking or follow-up.
        
        Args:
            fields: Comma-separated field names (first_name, last_name, email, phone)
            reason: Why we need this information
        """
        field_list = [f.strip() for f in fields.split(",")]
        result = collect_customer_info(
            self.customer_info,
            field_list,
            reason
        )
        
        if result["all_collected"]:
            self.pending_input_type = None
            self.pending_input_config = None
            return f"I have all your information. Thank you, {self.customer_info.get('first_name', 'valued customer')}!"
        
        self.collecting_field = result["missing_fields"][0] if result["missing_fields"] else None
        
        # Map internal field names to display names for the UI
        # Note: The frontend contact form only supports "name", "phone", "email" fields
        # Both first_name and last_name map to "name" field in the UI
        field_mapping = {"first_name": "name", "last_name": "name", "email": "email", "phone": "phone"}
        # Deduplicate fields (e.g., if both first_name and last_name requested, only show one "name" field)
        display_fields = list(dict.fromkeys([field_mapping.get(f, f) for f in result.get("missing_fields", ["name", "phone"])]))
        
        # Set up structured contact form input
        self.pending_input_type = "contact_form"
        self.pending_input_config = {"fields": display_fields}
        
        return result.get("prompt", "Could you please provide your contact information?")
    
    def update_customer_info(self, field: str, value: str) -> str:
        """Update collected customer information."""
        parsed = parse_customer_input(value, field)
        if parsed.get("valid"):
            self.customer_info[field] = parsed["value"]
            return "Got it, thank you!"
        return parsed.get("error", "Could you please try again?")
