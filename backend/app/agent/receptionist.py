"""AI Receptionist Agent implementation using Agno."""
from typing import Optional
import yaml

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

from app.config import settings

# Shared database for Agno session persistence
agno_db = SqliteDb(db_file=str(settings.DATABASE_PATH.parent / "agno_sessions.db"))
from app.agent.prompts import get_system_prompt
from app.tools.business_info import (
    get_business_hours, 
    get_service_details, 
    get_policies, 
    search_faqs,
    get_business_info
)
from app.tools.customer_info import collect_customer_info, parse_customer_input

# V2 Tools
from app.tools.booking import (
    check_availability as booking_check_availability,
    book_appointment as booking_book_appointment,
    cancel_appointment as booking_cancel_appointment,
    reschedule_appointment as booking_reschedule_appointment
)
from app.tools.leads import (
    capture_lead as leads_capture_lead,
    add_to_waitlist as leads_add_to_waitlist
)
from app.tools.customers import (
    identify_customer as customers_identify,
    get_customer_history as customers_get_history,
    create_or_update_customer,
    get_rebooking_suggestion,
    get_upcoming_appointments as customers_get_upcoming
)

# V3 Tools
from app.tools.recommendations import recommend_service as tools_recommend_service
from app.tools.workflows import execute_triggered_workflows


class ReceptionistToolkit:
    """Toolkit for the receptionist agent with business config context."""
    
    def __init__(self, business_config: dict, business_id: str = None):
        self.config = business_config
        self.business_id = business_id
        self.customer_info = {}
        self.current_customer_id = None  # For returning customers
        self.collecting_field = None
        self.pending_input_type = None  # Track what structured input to show
        self.pending_input_config = None
        self.selected_service_id = None  # Track selected service for booking
        self.selected_slot_id = None  # Track selected time slot
        self.pending_reschedule_appointment = None  # Track appointment being rescheduled
    
    def get_hours(self, day: Optional[str] = None) -> str:
        """Get business hours. Optionally specify a day (e.g., 'monday', 'saturday')."""
        result = get_business_hours(self.config, day)
        if "error" in result:
            return result["error"]
        if "day" in result:
            if result.get("status") == "closed":
                return f"We are closed on {result['day'].title()}."
            return f"On {result['day'].title()}, we're open from {result['open']} to {result['close']}."
        
        hours_list = []
        for d, h in result.get("hours", {}).items():
            if h.get("status") == "closed":
                hours_list.append(f"{d.title()}: Closed")
            else:
                hours_list.append(f"{d.title()}: {h['open']} - {h['close']}")
        return "Our hours are:\n" + "\n".join(hours_list)
    
    def get_services_list(self) -> list[dict]:
        """Get raw list of services for structured display."""
        services = self.config.get("services", [])
        return services
    
    def get_services(self, service_name: Optional[str] = None) -> str:
        """Get service information. Optionally search by service name."""
        result = get_service_details(self.config, service_name=service_name)
        if "error" in result and not result.get("services"):
            return result["error"]
        
        services = result.get("services", [result.get("service")] if result.get("service") else [])
        if not services:
            return "I couldn't find any services matching your request."
        
        service_info = []
        for s in services:
            info = f"**{s['name']}** - ${s['price']}"
            if s.get('duration_minutes'):
                info += f" ({s['duration_minutes']} min)"
            if s.get('description'):
                info += f"\n  {s['description']}"
            service_info.append(info)
        
        return "\n\n".join(service_info)
    
    def get_policy(self, policy_type: Optional[str] = None) -> str:
        """Get business policies. Optionally specify type (cancellation, deposit, walk_ins)."""
        result = get_policies(self.config, policy_type)
        if "error" in result:
            return result["error"]
        
        if "policy" in result:
            return f"Our {result['policy'].replace('_', ' ')} policy: {result['value']}"
        
        policies = result.get("policies", {})
        policy_info = []
        if policies.get("cancellation"):
            policy_info.append(f"**Cancellation:** {policies['cancellation']}")
        if policies.get("deposit"):
            policy_info.append(f"**Deposit:** ${policies.get('deposit_amount', 0)} required")
        if policies.get("walk_ins"):
            policy_info.append(f"**Walk-ins:** {policies['walk_ins']}")
        
        return "\n".join(policy_info) if policy_info else "No specific policies listed."
    
    def search_faq(self, query: str) -> str:
        """Search FAQs for answers to common questions."""
        result = search_faqs(self.config, query)
        matches = result.get("matches", [])
        
        if not matches:
            return "I couldn't find a specific FAQ about that. Let me try to help you directly."
        
        faq = matches[0]
        return f"**Q: {faq['question']}**\nA: {faq['answer']}"
    
    def get_location(self) -> str:
        """Get business location and contact information."""
        name = self.config.get("name", "Our business")
        location = self.config.get("location", "")
        phone = self.config.get("phone", "")
        email = self.config.get("email", "")
        
        info = [f"**{name}**"]
        if location:
            info.append(f"Address: {location}")
        if phone:
            info.append(f"Phone: {phone}")
        if email:
            info.append(f"Email: {email}")
        
        return "\n".join(info)
    
    def request_customer_info(self, fields: list[str], reason: str) -> str:
        """Request customer information for booking or inquiries."""
        result = collect_customer_info(
            self.customer_info,
            fields,
            reason
        )
        
        if result["all_collected"]:
            self.pending_input_type = None
            self.pending_input_config = None
            return f"I have all your information. Thank you, {self.customer_info.get('first_name', 'valued customer')}!"
        
        self.collecting_field = result["missing_fields"][0] if result["missing_fields"] else None
        
        # Set up structured contact form input
        self.pending_input_type = "contact_form"
        self.pending_input_config = {"fields": result.get("missing_fields", ["name", "phone"])}
        
        return result.get("prompt", "Could you please provide your contact information?")
    
    def update_customer_info(self, field: str, value: str) -> str:
        """Update collected customer information."""
        parsed = parse_customer_input(value, field)
        if parsed.get("valid"):
            self.customer_info[field] = parsed["value"]
            return f"Got it, thank you!"
        return parsed.get("error", "Could you please try again?")


def create_receptionist_agent(
    business_config: dict,
    business_name: str,
    business_type: str,
    business_id: str = None
) -> tuple[Agent, ReceptionistToolkit]:
    """
    Create a receptionist agent for a specific business.
    
    Args:
        business_config: The parsed YAML business configuration
        business_name: Name of the business
        business_type: Type/vertical of the business
        business_id: Business ID for V2 tools
        
    Returns:
        Tuple of (Agent, ReceptionistToolkit)
    """
    toolkit = ReceptionistToolkit(business_config, business_id)
    
    model = OpenAIChat(
        id=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    
    from agno.tools import tool
    
    # ============ V1 Tools ============
    
    @tool
    def get_business_hours_tool(day: Optional[str] = None) -> str:
        """Get business operating hours. Optionally specify a day like 'monday' or 'saturday'."""
        return toolkit.get_hours(day)
    
    @tool
    def get_services_tool(service_name: Optional[str] = None) -> str:
        """Get information about services offered. Optionally search by service name."""
        # If searching for a specific service, just return text info
        if service_name:
            return toolkit.get_services(service_name)
        
        # If listing all services, show the structured service selector UI
        services_list = toolkit.get_services_list()
        if services_list:
            toolkit.pending_input_type = "service_select"
            toolkit.pending_input_config = {
                "services": services_list,
                "multi_select": False
            }
            return "Here are our services. Select one to learn more or book an appointment:"
        
        return toolkit.get_services(service_name)
    
    @tool
    def get_policies_tool(policy_type: Optional[str] = None) -> str:
        """Get business policies. Types: cancellation, deposit, walk_ins."""
        return toolkit.get_policy(policy_type)
    
    @tool
    def search_faqs_tool(query: str) -> str:
        """Search frequently asked questions for answers."""
        return toolkit.search_faq(query)
    
    @tool
    def get_location_tool() -> str:
        """Get business location and contact information."""
        return toolkit.get_location()
    
    @tool
    def collect_customer_info_tool(fields: str, reason: str) -> str:
        """
        Collect customer information for booking or follow-up.
        Fields should be comma-separated: first_name, last_name, email, phone
        """
        field_list = [f.strip() for f in fields.split(",")]
        return toolkit.request_customer_info(field_list, reason)
    
    @tool
    def start_booking_flow_tool() -> str:
        """
        Start the appointment booking process. 
        Call this when a customer wants to book an appointment.
        Returns available services so customer can choose.
        """
        services_list = toolkit.get_services_list()
        
        # Set up structured service selection input - don't list services in text
        toolkit.pending_input_type = "service_select"
        toolkit.pending_input_config = {
            "services": services_list,
            "multi_select": False
        }
        
        return "Great! Please select a service from the options below:"
    
    # ============ V2 Tools ============
    
    @tool
    def check_availability_tool(service_id: Optional[str] = None, date_range: str = "this week", time_preference: Optional[str] = None, staff_id: Optional[str] = None) -> str:
        """
        Check available appointment slots for a service.
        
        Args:
            service_id: ID of the service to book (e.g., 'womens_haircut', 'mens_haircut'). Optional - uses previously selected service if not provided.
            date_range: When to look for slots (e.g., 'this week', 'tomorrow', 'next week'). Defaults to 'this week'.
            time_preference: Preferred time (e.g., 'morning', 'afternoon', 'after 5pm')
            staff_id: Optional specific staff member ID
        
        Returns available time slots that can be presented to the customer.
        IMPORTANT: Call this immediately after customer selects a service - the service_id is already tracked.
        """
        if not toolkit.business_id:
            return "Booking is not available at this time."
        
        # Use stored service_id if not provided
        actual_service_id = service_id or toolkit.selected_service_id
        if not actual_service_id:
            return "Please select a service first before checking availability."
        
        result = booking_check_availability(
            business_id=toolkit.business_id,
            service_id=actual_service_id,
            date_range=date_range,
            time_preference=time_preference,
            staff_id=staff_id,
            config=toolkit.config
        )
        
        if 'error' in result:
            return result['error']
        
        slots = result.get('slots', [])
        if not slots:
            return f"I'm sorry, there are no available slots for {result.get('service_name', 'this service')} during {date_range}. Would you like to try a different time or be added to our waitlist?"
        
        # Store service for booking
        toolkit.selected_service_id = actual_service_id
        
        # Set up calendar UI with all available slots
        toolkit.pending_input_type = "datetime_picker"
        toolkit.pending_input_config = {
            "min_date": result['calendar_ui_data'].get('min_date'),
            "max_date": result['calendar_ui_data'].get('max_date'),
            "available_dates": result['calendar_ui_data'].get('available_dates', []),
            "time_slots": result['calendar_ui_data'].get('time_slots', []),
            "slots": slots
        }
        
        # Don't list specific times in text - let the datetime picker UI show them
        # This prevents mismatch between AI text and actual available slots
        service_name = result.get('service_name', 'your appointment')
        return f"I found {len(slots)} available time slots for {service_name}. Please select your preferred date and time from the calendar below."
    
    @tool
    def book_appointment_tool(customer_name: str, customer_phone: str, slot_id: Optional[str] = None, customer_email: Optional[str] = None) -> str:
        """
        Book a confirmed appointment.
        
        Args:
            customer_name: Customer's full name
            customer_phone: Customer's phone number  
            slot_id: The slot ID (optional - uses the time slot customer selected from calendar)
            customer_email: Customer's email (optional)
        
        Call this after customer has selected a time slot and provided their name and phone.
        The slot_id is automatically tracked from the customer's time selection.
        """
        if not toolkit.business_id or not toolkit.selected_service_id:
            return "Please select a service and time first."
        
        # Use stored slot_id if not provided
        actual_slot_id = slot_id or toolkit.selected_slot_id
        if not actual_slot_id:
            return "Please select a time slot first before booking."
        
        result = booking_book_appointment(
            business_id=toolkit.business_id,
            service_id=toolkit.selected_service_id,
            slot_id=actual_slot_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            customer_id=toolkit.current_customer_id,
            config=toolkit.config
        )
        
        if 'error' in result:
            return result['error']
        
        # Clear booking state
        toolkit.selected_service_id = None
        toolkit.selected_slot_id = None
        
        # Store customer info
        toolkit.customer_info['first_name'] = customer_name.split()[0]
        toolkit.customer_info['phone'] = customer_phone
        if customer_email:
            toolkit.customer_info['email'] = customer_email
        
        return result['message'] + f"\n\nConfirmation #: {result['confirmation_id'][:8].upper()}"
    
    @tool
    def cancel_appointment_tool(customer_phone: str, appointment_id: Optional[str] = None) -> str:
        """
        Cancel an existing appointment.
        
        Args:
            customer_phone: Customer's phone number to find their appointment
            appointment_id: Optional specific appointment ID if known
        """
        if not toolkit.business_id:
            return "Cancellation is not available at this time."
        
        result = booking_cancel_appointment(
            business_id=toolkit.business_id,
            customer_phone=customer_phone,
            appointment_id=appointment_id
        )
        
        return result['message']
    
    @tool
    def reschedule_appointment_tool(appointment_id: Optional[str] = None, new_slot_id: Optional[str] = None) -> str:
        """
        Reschedule an existing appointment to a new time.
        
        Args:
            appointment_id: The appointment ID to reschedule (optional - uses tracked appointment from get_upcoming_appointments_tool)
            new_slot_id: New time slot ID (optional - uses tracked slot from calendar selection)
        
        Call this after:
        1. Using get_upcoming_appointments_tool to find the appointment
        2. Using check_availability_tool to show new times
        3. Customer selects a new time from the calendar
        
        The IDs are automatically tracked from previous tool calls.
        """
        if not toolkit.business_id:
            return "Rescheduling is not available at this time."
        
        # Use tracked appointment ID if not provided
        actual_appointment_id = appointment_id
        if not actual_appointment_id and toolkit.pending_reschedule_appointment:
            actual_appointment_id = toolkit.pending_reschedule_appointment.get('appointment_id')
        
        if not actual_appointment_id:
            return "No appointment found to reschedule. Please use get_upcoming_appointments_tool first to find the appointment."
        
        # Use tracked slot ID if not provided
        actual_slot_id = new_slot_id or toolkit.selected_slot_id
        if not actual_slot_id:
            return "Please select a new time slot from the calendar first."
        
        result = booking_reschedule_appointment(
            business_id=toolkit.business_id,
            appointment_id=actual_appointment_id,
            new_slot_id=actual_slot_id
        )
        
        if 'error' in result:
            return result['error']
        
        # Clear reschedule state
        toolkit.pending_reschedule_appointment = None
        toolkit.selected_slot_id = None
        toolkit.selected_service_id = None
        
        return result['message']
    
    @tool
    def capture_lead_tool(name: str, interest: str, email: Optional[str] = None, phone: Optional[str] = None, company: Optional[str] = None, notes: Optional[str] = None) -> str:
        """
        Capture a sales lead for follow-up.
        
        Use this when customer is interested in:
        - Corporate/group packages
        - Consultation services
        - Custom quotes
        - Membership inquiries
        - Any service requiring sales follow-up
        
        Args:
            name: Lead's name
            interest: What they're interested in
            email: Email address
            phone: Phone number
            company: Company name (for B2B)
            notes: Additional notes
        """
        if not toolkit.business_id:
            return "Lead capture is not available at this time."
        
        result = leads_capture_lead(
            business_id=toolkit.business_id,
            name=name,
            interest=interest,
            email=email,
            phone=phone,
            company=company,
            notes=notes
        )
        
        if 'error' in result:
            return result['error']
        
        return result['message']
    
    @tool
    def add_to_waitlist_tool(service_id: str, customer_name: str, customer_contact: str, preferred_dates: str, preferred_times: str, contact_method: str = "phone") -> str:
        """
        Add customer to waitlist when no slots are available.
        
        Args:
            service_id: Service ID they want
            customer_name: Customer's name
            customer_contact: Phone or email based on contact_method
            preferred_dates: Comma-separated preferred dates (e.g., "2024-12-15, 2024-12-16")
            preferred_times: Comma-separated preferred times (e.g., "morning, afternoon")
            contact_method: How to contact them (phone, email, sms)
        """
        if not toolkit.business_id:
            return "Waitlist is not available at this time."
        
        dates = [d.strip() for d in preferred_dates.split(",")]
        times = [t.strip() for t in preferred_times.split(",")]
        
        result = leads_add_to_waitlist(
            business_id=toolkit.business_id,
            service_id=service_id,
            customer_name=customer_name,
            customer_contact=customer_contact,
            preferred_dates=dates,
            preferred_times=times,
            contact_method=contact_method,
            customer_id=toolkit.current_customer_id
        )
        
        return result['message']
    
    @tool
    def identify_customer_tool(phone: Optional[str] = None, email: Optional[str] = None) -> str:
        """
        Identify if a customer is new or returning.
        
        Call this when you learn a customer's phone or email to personalize the experience.
        Returns welcome message with visit history for returning customers.
        
        Args:
            phone: Customer's phone number
            email: Customer's email address
        """
        if not toolkit.business_id:
            return "Customer identification is not available."
        
        result = customers_identify(
            business_id=toolkit.business_id,
            phone=phone,
            email=email
        )
        
        if result.get('customer_id'):
            toolkit.current_customer_id = result['customer_id']
            toolkit.customer_info['first_name'] = result.get('first_name', result.get('name', '').split()[0])
        
        return result['message']
    
    @tool
    def get_upcoming_appointments_tool(customer_phone: str) -> str:
        """
        Get upcoming appointments for a customer by their phone number.
        
        Use this when a customer wants to reschedule or check their upcoming appointments.
        Returns appointment details including appointment_id needed for rescheduling.
        
        Args:
            customer_phone: Customer's phone number
        """
        if not toolkit.business_id:
            return "Appointment lookup is not available."
        
        result = customers_get_upcoming(
            business_id=toolkit.business_id,
            customer_phone=customer_phone
        )
        
        appointments = result.get('appointments', [])
        if not appointments:
            return result['message']
        
        # Store first appointment for potential rescheduling
        if appointments:
            toolkit.pending_reschedule_appointment = appointments[0]
            toolkit.selected_service_id = appointments[0]['service_id']
        
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
    
    @tool
    def get_customer_history_tool(customer_id: Optional[str] = None) -> str:
        """
        Get visit history for a returning customer.
        
        Args:
            customer_id: Customer ID (uses current if not provided)
        """
        if not toolkit.business_id:
            return "Customer history is not available."
        
        cust_id = customer_id or toolkit.current_customer_id
        if not cust_id:
            return "No customer identified yet. Please provide a phone number or email first."
        
        result = customers_get_history(
            business_id=toolkit.business_id,
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
            history.append(f"- {visit['date']}: {visit['service']}" + (f" with {visit['staff_name']}" if visit.get('staff_name') else ""))
        
        return "\n".join(history)
    
    @tool
    def suggest_rebooking_tool() -> str:
        """
        Get a rebooking suggestion for the current returning customer.
        
        Call this for returning customers to suggest their next appointment
        based on their visit history and frequency.
        """
        if not toolkit.business_id or not toolkit.current_customer_id:
            return "Please identify the customer first to get rebooking suggestions."
        
        result = get_rebooking_suggestion(
            business_id=toolkit.business_id,
            customer_id=toolkit.current_customer_id
        )
        
        if 'error' in result:
            return result['error']
        
        if result.get('suggestion'):
            toolkit.selected_service_id = result['suggestion'].get('service_id')
        
        return result.get('message', "Would you like to book your next appointment?")
    
    # ============ V3 Tools ============
    
    @tool
    def recommend_service_tool(goals: str, concerns: Optional[str] = None, preferences: Optional[str] = None, budget: Optional[str] = None) -> str:
        """
        Recommend services based on customer's goals, concerns, and preferences.
        
        Use this when a customer describes what they want to achieve but isn't sure
        which service to book. This helps match their needs to your service offerings.
        
        Args:
            goals: What the customer wants to achieve (e.g., "relax", "look refreshed", "pain relief")
            concerns: Specific issues they want to address (e.g., "wrinkles", "back pain", "acne")
            preferences: Any preferences (e.g., "quick", "natural", "non-invasive")
            budget: Budget indication (e.g., "under $100", "premium")
        
        Returns personalized service recommendations with explanations.
        """
        if not toolkit.business_id:
            return "I can help you find the right service. Could you tell me more about what you're looking for?"
        
        result = tools_recommend_service(
            business_id=toolkit.business_id,
            goals=goals,
            concerns=concerns,
            preferences=preferences,
            budget=budget,
            config=toolkit.config
        )
        
        recommendations = result.get('recommendations', [])
        if recommendations and len(recommendations) > 0:
            toolkit.selected_service_id = recommendations[0]['service_id']
        
        return result.get('message', "Let me help you find the right service for your needs.")
    
    @tool
    def check_for_special_offers_tool(message: str) -> str:
        """
        Check if the customer's message triggers any special offers or workflows.
        
        This automatically checks for things like:
        - Birthday mentions (birthday discounts)
        - Wedding/bridal inquiries (special packages)
        - Corporate inquiries (B2B capture)
        - Loyalty rewards for returning customers
        
        Args:
            message: The customer's message to check for triggers
        
        Call this internally when you detect the customer might be eligible for a special offer.
        """
        if not toolkit.business_id:
            return ""
        
        customer_data = {
            'is_returning': toolkit.current_customer_id is not None,
            'visit_count': toolkit.customer_info.get('visit_count', 0),
            'first_name': toolkit.customer_info.get('first_name'),
            'is_first_message': False
        }
        
        result = execute_triggered_workflows(
            business_id=toolkit.business_id,
            message=message,
            customer_data=customer_data,
            context={'customer_info': toolkit.customer_info}
        )
        
        if not result.get('triggered'):
            return ""
        
        messages = result.get('messages', [])
        discounts = result.get('discounts', [])
        
        response_parts = []
        if messages:
            response_parts.extend(messages)
        if discounts:
            for d in discounts:
                response_parts.append(f"Use code **{d['code']}** for {d['percent']}% off!")
        
        return "\n\n".join(response_parts) if response_parts else ""
    
    # Build tool list
    v1_tools = [
        get_business_hours_tool,
        get_services_tool,
        get_policies_tool,
        search_faqs_tool,
        get_location_tool,
        collect_customer_info_tool,
        start_booking_flow_tool,
    ]
    
    v2_tools = [
        check_availability_tool,
        book_appointment_tool,
        cancel_appointment_tool,
        reschedule_appointment_tool,
        capture_lead_tool,
        add_to_waitlist_tool,
        identify_customer_tool,
        get_upcoming_appointments_tool,
        get_customer_history_tool,
        suggest_rebooking_tool,
    ]
    
    v3_tools = [
        recommend_service_tool,
        check_for_special_offers_tool,
    ]
    
    all_tools = v1_tools + v2_tools + v3_tools
    
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
    
    return agent, toolkit


def load_business_config(config_yaml: str) -> dict:
    """Load and parse business configuration from YAML string."""
    if not config_yaml:
        return {}
    try:
        return yaml.safe_load(config_yaml) or {}
    except yaml.YAMLError:
        return {}
