"""AI Receptionist Agent implementation using Agno - Refactored Version."""
from typing import Optional
import yaml

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.tools import tool

from app.config import settings
from app.agent.prompts import get_system_prompt
from app.agent.toolkits import (
    BusinessInfoToolkit,
    BookingToolkit,
    CustomerToolkit,
    LeadsToolkit,
)

# Shared database for Agno session persistence
agno_db = SqliteDb(db_file=str(settings.DATABASE_PATH.parent / "agno_sessions.db"))


class ReceptionistToolkits:
    """Container for all receptionist toolkits with shared state management."""
    
    def __init__(self, business_id: str, config: dict):
        self.business_id = business_id
        self.config = config
        
        # Initialize toolkits
        self.business_info = BusinessInfoToolkit(config=config)
        self.booking = BookingToolkit(business_id=business_id, config=config)
        self.customer = CustomerToolkit(business_id=business_id)
        self.leads = LeadsToolkit(business_id=business_id, config=config)
    
    @property
    def pending_input_type(self) -> Optional[str]:
        """Get pending input type - customer form takes priority when set."""
        # Customer form should take priority when collecting contact info
        if self.customer.pending_input_type == "contact_form":
            return self.customer.pending_input_type
        return (
            self.booking.pending_input_type or 
            self.customer.pending_input_type
        )
    
    @property
    def pending_input_config(self) -> Optional[dict]:
        """Get pending input config - matches the input type priority."""
        if self.customer.pending_input_type == "contact_form":
            return self.customer.pending_input_config
        return (
            self.booking.pending_input_config or 
            self.customer.pending_input_config
        )
    
    def clear_pending_input(self):
        """Clear pending input from all toolkits."""
        self.booking.pending_input_type = None
        self.booking.pending_input_config = None
        self.customer.pending_input_type = None
        self.customer.pending_input_config = None
    
    @property
    def selected_service_id(self) -> Optional[str]:
        return self.booking.selected_service_id
    
    @selected_service_id.setter
    def selected_service_id(self, value: str):
        self.booking.selected_service_id = value
    
    @property
    def selected_slot_id(self) -> Optional[str]:
        return self.booking.selected_slot_id
    
    @selected_slot_id.setter
    def selected_slot_id(self, value: str):
        self.booking.selected_slot_id = value
    
    @property
    def customer_info(self) -> dict:
        return self.customer.customer_info
    
    @property
    def current_customer_id(self) -> Optional[str]:
        return self.customer.current_customer_id
    
    @property
    def collecting_field(self) -> Optional[str]:
        return self.customer.collecting_field
    
    @property
    def pending_reschedule_appointment(self) -> Optional[dict]:
        return self.booking.pending_reschedule_appointment
    
    @pending_reschedule_appointment.setter
    def pending_reschedule_appointment(self, value: dict):
        self.booking.pending_reschedule_appointment = value


def create_receptionist_agent(
    business_config: dict,
    business_name: str,
    business_type: str,
    business_id: str = None
) -> tuple[Agent, ReceptionistToolkits]:
    """
    Create a receptionist agent for a specific business.
    
    Args:
        business_config: The parsed YAML business configuration
        business_name: Name of the business
        business_type: Type/vertical of the business
        business_id: Business ID for booking tools
        
    Returns:
        Tuple of (Agent, ReceptionistToolkits)
    """
    toolkits = ReceptionistToolkits(business_id, business_config)
    
    model = OpenAIChat(
        id=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    
    # Create wrapper tools that bridge toolkits with proper function signatures
    # These tools use the toolkit state and set UI configs
    
    @tool
    def get_business_hours(day: Optional[str] = None) -> str:
        """Get business operating hours. Optionally specify a day like 'monday' or 'saturday'."""
        return toolkits.business_info.get_business_hours(day)
    
    @tool
    def get_services(service_name: Optional[str] = None) -> str:
        """Get information about services offered. Optionally search by service name."""
        if service_name:
            return toolkits.business_info.get_services(service_name)
        
        # Show service selector UI
        services_list = toolkits.business_info.get_services_list()
        if services_list:
            toolkits.booking.pending_input_type = "service_select"
            toolkits.booking.pending_input_config = {
                "services": services_list,
                "multi_select": False
            }
            return "Here are our services. Select one to learn more or book an appointment:"
        
        return toolkits.business_info.get_services(service_name)
    
    @tool
    def get_policies(policy_type: Optional[str] = None) -> str:
        """Get business policies. Types: cancellation, deposit, walk_ins."""
        return toolkits.business_info.get_policies(policy_type)
    
    @tool
    def search_faqs(query: str) -> str:
        """Search frequently asked questions for answers."""
        return toolkits.business_info.search_faqs(query)
    
    @tool
    def get_location() -> str:
        """Get business location and contact information."""
        return toolkits.business_info.get_location()
    
    @tool
    def start_booking_flow() -> str:
        """Start the appointment booking process. Shows service selection UI."""
        services_list = toolkits.business_info.get_services_list()
        return toolkits.booking.start_booking_flow(services_list)
    
    @tool
    def check_availability(
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
        return toolkits.booking.check_availability(
            service_id=service_id,
            date_range=date_range,
            time_preference=time_preference,
            staff_id=staff_id
        )
    
    @tool
    def book_appointment(
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
        result = toolkits.booking.book_appointment(
            customer_name=customer_name,
            customer_phone=customer_phone,
            slot_id=slot_id,
            customer_email=customer_email
        )
        
        # Update customer info
        if 'error' not in result:
            toolkits.customer.customer_info['first_name'] = customer_name.split()[0]
            toolkits.customer.customer_info['phone'] = customer_phone
            if customer_email:
                toolkits.customer.customer_info['email'] = customer_email
        
        return result
    
    @tool
    def cancel_appointment(
        customer_phone: str,
        appointment_id: Optional[str] = None
    ) -> str:
        """Cancel an existing appointment."""
        return toolkits.booking.cancel_appointment(
            customer_phone=customer_phone,
            appointment_id=appointment_id
        )
    
    @tool
    def reschedule_appointment(
        appointment_id: Optional[str] = None,
        new_slot_id: Optional[str] = None
    ) -> str:
        """Reschedule an existing appointment to a new time."""
        return toolkits.booking.reschedule_appointment(
            appointment_id=appointment_id,
            new_slot_id=new_slot_id
        )
    
    @tool
    def identify_customer(
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> str:
        """Identify if a customer is new or returning."""
        return toolkits.customer.identify_customer(phone=phone, email=email)
    
    @tool
    def get_upcoming_appointments(customer_phone: str) -> str:
        """Get upcoming appointments for a customer by their phone number."""
        result = toolkits.customer.get_upcoming_appointments(customer_phone)
        
        # Sync appointment info to booking toolkit for rescheduling
        if hasattr(toolkits.customer, '_pending_reschedule_appointment'):
            toolkits.booking.pending_reschedule_appointment = toolkits.customer._pending_reschedule_appointment
        if hasattr(toolkits.customer, '_selected_service_id'):
            toolkits.booking.selected_service_id = toolkits.customer._selected_service_id
        
        return result
    
    @tool
    def get_customer_history(customer_id: Optional[str] = None) -> str:
        """Get visit history for a returning customer."""
        return toolkits.customer.get_customer_history(customer_id)
    
    @tool
    def suggest_rebooking() -> str:
        """Get a rebooking suggestion for the current returning customer."""
        return toolkits.customer.suggest_rebooking()
    
    @tool
    def collect_customer_info(fields: str, reason: str) -> str:
        """
        Collect customer information for booking or follow-up.
        Fields should be comma-separated: first_name, last_name, email, phone
        """
        return toolkits.customer.collect_customer_info(fields, reason)
    
    @tool
    def capture_lead(
        name: str,
        interest: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Capture a sales lead for follow-up."""
        return toolkits.leads.capture_lead(
            name=name,
            interest=interest,
            email=email,
            phone=phone,
            company=company,
            notes=notes
        )
    
    @tool
    def add_to_waitlist(
        service_id: str,
        customer_name: str,
        customer_contact: str,
        preferred_dates: str,
        preferred_times: str,
        contact_method: str = "phone"
    ) -> str:
        """Add customer to waitlist when no slots are available."""
        return toolkits.leads.add_to_waitlist(
            service_id=service_id,
            customer_name=customer_name,
            customer_contact=customer_contact,
            preferred_dates=preferred_dates,
            preferred_times=preferred_times,
            contact_method=contact_method,
            customer_id=toolkits.current_customer_id
        )
    
    @tool
    def recommend_service(
        goals: str,
        concerns: Optional[str] = None,
        preferences: Optional[str] = None,
        budget: Optional[str] = None
    ) -> str:
        """Recommend services based on customer's goals, concerns, and preferences."""
        return toolkits.leads.recommend_service(
            goals=goals,
            concerns=concerns,
            preferences=preferences,
            budget=budget
        )
    
    @tool
    def check_for_special_offers(message: str) -> str:
        """Check if the customer's message triggers any special offers."""
        return toolkits.leads.check_for_special_offers(
            message=message,
            customer_info=toolkits.customer_info,
            is_returning=toolkits.current_customer_id is not None
        )
    
    # Collect all tools
    all_tools = [
        # Business info
        get_business_hours,
        get_services,
        get_policies,
        search_faqs,
        get_location,
        # Booking
        start_booking_flow,
        check_availability,
        book_appointment,
        cancel_appointment,
        reschedule_appointment,
        # Customer
        identify_customer,
        get_upcoming_appointments,
        get_customer_history,
        suggest_rebooking,
        collect_customer_info,
        # Leads
        capture_lead,
        add_to_waitlist,
        recommend_service,
        check_for_special_offers,
    ]
    
    agent = Agent(
        name=f"{business_name} Receptionist",
        model=model,
        instructions=get_system_prompt(business_name, business_type),
        tools=all_tools,
        markdown=True,
        db=agno_db,
        add_history_to_context=True,
        num_history_runs=10,
    )
    
    return agent, toolkits


def load_business_config(config_yaml: str) -> dict:
    """Load and parse business configuration from YAML string."""
    if not config_yaml:
        return {}
    try:
        return yaml.safe_load(config_yaml) or {}
    except yaml.YAMLError:
        return {}
