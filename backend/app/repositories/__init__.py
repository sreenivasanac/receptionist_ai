"""Repository layer for data access."""
from app.repositories.staff import StaffRepository
from app.repositories.services import ServiceRepository
from app.repositories.customers import CustomerRepository
from app.repositories.appointments import AppointmentRepository
from app.repositories.leads import LeadRepository
from app.repositories.waitlist import WaitlistRepository
from app.repositories.campaigns import CampaignRepository
from app.repositories.business import BusinessRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.users import UserRepository

# Singleton instances for easy importing
staff_repo = StaffRepository()
service_repo = ServiceRepository()
customer_repo = CustomerRepository()
appointment_repo = AppointmentRepository()
lead_repo = LeadRepository()
waitlist_repo = WaitlistRepository()
campaign_repo = CampaignRepository()
business_repo = BusinessRepository()
conversation_repo = ConversationRepository()
user_repo = UserRepository()

__all__ = [
    "StaffRepository",
    "ServiceRepository", 
    "CustomerRepository",
    "AppointmentRepository",
    "LeadRepository",
    "WaitlistRepository",
    "CampaignRepository",
    "BusinessRepository",
    "ConversationRepository",
    "UserRepository",
    "staff_repo",
    "service_repo",
    "customer_repo",
    "appointment_repo",
    "lead_repo",
    "waitlist_repo",
    "campaign_repo",
    "business_repo",
    "conversation_repo",
    "user_repo",
]
