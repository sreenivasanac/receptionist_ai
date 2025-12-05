"""Business information toolkit - hours, services, policies, FAQs, location."""
from typing import Optional

from agno.tools import Toolkit

from app.tools.business_info import (
    get_business_hours,
    get_service_details,
    get_policies,
    search_faqs,
)


class BusinessInfoToolkit(Toolkit):
    """Toolkit for business information queries."""
    
    def __init__(self, config: dict, **kwargs):
        self.config = config
        tools = [
            self.get_business_hours,
            self.get_services,
            self.get_policies,
            self.search_faqs,
            self.get_location,
            self.get_services_list,
        ]
        super().__init__(name="business_info_tools", tools=tools, **kwargs)
    
    def get_business_hours(self, day: Optional[str] = None) -> str:
        """Get business operating hours. Optionally specify a day like 'monday' or 'saturday'."""
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
        """Get information about services offered. Optionally search by service name."""
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
    
    def get_services_list(self) -> list[dict]:
        """Get raw list of services for structured display."""
        return self.config.get("services", [])
    
    def get_policies(self, policy_type: Optional[str] = None) -> str:
        """Get business policies. Types: cancellation, deposit, walk_ins."""
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
    
    def search_faqs(self, query: str) -> str:
        """Search frequently asked questions for answers."""
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
