"""Leads toolkit - capture leads, waitlist, recommendations."""
from typing import Optional

from agno.tools import Toolkit

from app.tools.leads import (
    capture_lead as leads_capture_lead,
    add_to_waitlist as leads_add_to_waitlist,
)
from app.tools.recommendations import recommend_service as tools_recommend_service
from app.tools.workflows import execute_triggered_workflows


class LeadsToolkit(Toolkit):
    """Toolkit for lead capture, waitlist, and recommendations."""
    
    def __init__(self, business_id: str, config: dict, **kwargs):
        self.business_id = business_id
        self.config = config
        
        tools = [
            self.capture_lead,
            self.add_to_waitlist,
            self.recommend_service,
            self.check_for_special_offers,
        ]
        super().__init__(name="leads_tools", tools=tools, **kwargs)
    
    def capture_lead(
        self,
        name: str,
        interest: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Capture a sales lead for follow-up.
        
        Use this when customer is interested in:
        - Corporate/group packages
        - Consultation services
        - Custom quotes
        - Membership inquiries
        
        Args:
            name: Lead's name
            interest: What they're interested in
            email: Email address
            phone: Phone number
            company: Company name (for B2B)
            notes: Additional notes
        """
        if not self.business_id:
            return "Lead capture is not available at this time."
        
        result = leads_capture_lead(
            business_id=self.business_id,
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
    
    def add_to_waitlist(
        self,
        service_id: str,
        customer_name: str,
        customer_contact: str,
        preferred_dates: str,
        preferred_times: str,
        contact_method: str = "phone",
        customer_id: Optional[str] = None
    ) -> str:
        """
        Add customer to waitlist when no slots are available.
        
        Args:
            service_id: Service ID they want
            customer_name: Customer's name
            customer_contact: Phone or email
            preferred_dates: Comma-separated preferred dates
            preferred_times: Comma-separated preferred times
            contact_method: How to contact them (phone, email, sms)
            customer_id: Optional customer ID if known
        """
        if not self.business_id:
            return "Waitlist is not available at this time."
        
        dates = [d.strip() for d in preferred_dates.split(",")]
        times = [t.strip() for t in preferred_times.split(",")]
        
        result = leads_add_to_waitlist(
            business_id=self.business_id,
            service_id=service_id,
            customer_name=customer_name,
            customer_contact=customer_contact,
            preferred_dates=dates,
            preferred_times=times,
            contact_method=contact_method,
            customer_id=customer_id
        )
        
        return result['message']
    
    def recommend_service(
        self,
        goals: str,
        concerns: Optional[str] = None,
        preferences: Optional[str] = None,
        budget: Optional[str] = None
    ) -> str:
        """
        Recommend services based on customer's goals, concerns, and preferences.
        
        Args:
            goals: What the customer wants to achieve
            concerns: Specific issues they want to address
            preferences: Any preferences (e.g., "quick", "natural")
            budget: Budget indication
        """
        if not self.business_id:
            return "I can help you find the right service. Could you tell me more?"
        
        result = tools_recommend_service(
            business_id=self.business_id,
            goals=goals,
            concerns=concerns,
            preferences=preferences,
            budget=budget,
            config=self.config
        )
        
        return result.get('message', "Let me help you find the right service for your needs.")
    
    def check_for_special_offers(
        self,
        message: str,
        customer_info: dict,
        is_returning: bool = False
    ) -> str:
        """
        Check if the customer's message triggers any special offers.
        
        Args:
            message: The customer's message to check
            customer_info: Current customer info dict
            is_returning: Whether customer is a returning customer
        """
        if not self.business_id:
            return ""
        
        customer_data = {
            'is_returning': is_returning,
            'visit_count': customer_info.get('visit_count', 0),
            'first_name': customer_info.get('first_name'),
            'is_first_message': False
        }
        
        result = execute_triggered_workflows(
            business_id=self.business_id,
            message=message,
            customer_data=customer_data,
            context={'customer_info': customer_info}
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
