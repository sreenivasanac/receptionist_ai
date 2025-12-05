"""Pydantic models for the API."""
from .business import Business, BusinessCreate, BusinessUpdate, BusinessConfig
from .user import User, UserCreate, UserLogin
from .service import Service, ServiceCreate
from .staff import Staff, StaffCreate
from .conversation import Conversation, ChatMessage, ChatRequest, ChatResponse

__all__ = [
    "Business", "BusinessCreate", "BusinessUpdate", "BusinessConfig",
    "User", "UserCreate", "UserLogin",
    "Service", "ServiceCreate",
    "Staff", "StaffCreate",
    "Conversation", "ChatMessage", "ChatRequest", "ChatResponse",
]
