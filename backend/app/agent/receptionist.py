"""AI Receptionist Agent implementation using Agno."""
from typing import Optional
import yaml

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from app.config import settings
from app.agent.prompts import get_system_prompt
from app.tools.business_info import (
    get_business_hours, 
    get_service_details, 
    get_policies, 
    search_faqs,
    get_business_info
)
from app.tools.customer_info import collect_customer_info, parse_customer_input


class ReceptionistToolkit:
    """Toolkit for the receptionist agent with business config context."""
    
    def __init__(self, business_config: dict):
        self.config = business_config
        self.customer_info = {}
        self.collecting_field = None
    
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
            return f"I have all your information. Thank you, {self.customer_info.get('first_name', 'valued customer')}!"
        
        self.collecting_field = result["missing_fields"][0] if result["missing_fields"] else None
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
    business_type: str
) -> tuple[Agent, ReceptionistToolkit]:
    """
    Create a receptionist agent for a specific business.
    
    Args:
        business_config: The parsed YAML business configuration
        business_name: Name of the business
        business_type: Type/vertical of the business
        
    Returns:
        Tuple of (Agent, ReceptionistToolkit)
    """
    toolkit = ReceptionistToolkit(business_config)
    
    model = OpenAIChat(
        id=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )
    
    from agno.tools import tool
    
    @tool
    def get_business_hours_tool(day: Optional[str] = None) -> str:
        """Get business operating hours. Optionally specify a day like 'monday' or 'saturday'."""
        return toolkit.get_hours(day)
    
    @tool
    def get_services_tool(service_name: Optional[str] = None) -> str:
        """Get information about services offered. Optionally search by service name."""
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
    
    agent = Agent(
        name=f"{business_name} Receptionist",
        model=model,
        instructions=get_system_prompt(business_name, business_type),
        tools=[
            get_business_hours_tool,
            get_services_tool,
            get_policies_tool,
            search_faqs_tool,
            get_location_tool,
            collect_customer_info_tool,
        ],
        markdown=True,
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
