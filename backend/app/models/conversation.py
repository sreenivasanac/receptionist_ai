"""Conversation and chat models."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class CustomerInfo(BaseModel):
    """Customer information collected during chat."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request from widget."""
    business_id: str
    session_id: str
    message: str
    customer_info: Optional[CustomerInfo] = None


class ChatResponse(BaseModel):
    """Chat response to widget."""
    session_id: str
    message: str
    customer_info_needed: list[str] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)


class Conversation(BaseModel):
    """Conversation session."""
    id: str
    business_id: str
    session_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    customer_info: CustomerInfo = Field(default_factory=CustomerInfo)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
