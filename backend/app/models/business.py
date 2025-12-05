"""Business models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BusinessHours(BaseModel):
    """Business hours for a single day."""
    open: Optional[str] = None
    close: Optional[str] = None
    closed: bool = False


class ServiceConfig(BaseModel):
    """Service configuration in YAML."""
    id: str
    name: str
    duration_minutes: int = 30
    price: float = 0
    description: str = ""


class PolicyConfig(BaseModel):
    """Business policies configuration."""
    cancellation: str = ""
    deposit: bool = False
    deposit_amount: float = 0
    walk_ins: str = ""


class FAQConfig(BaseModel):
    """FAQ item configuration."""
    question: str
    answer: str


class BusinessConfig(BaseModel):
    """Full business configuration stored as YAML."""
    business_id: str = ""
    name: str = ""
    location: str = ""
    phone: str = ""
    email: str = ""
    hours: dict[str, BusinessHours] = Field(default_factory=dict)
    services: list[ServiceConfig] = Field(default_factory=list)
    policies: PolicyConfig = Field(default_factory=PolicyConfig)
    faqs: list[FAQConfig] = Field(default_factory=list)


class BusinessCreate(BaseModel):
    """Business creation schema."""
    name: str
    type: str  # vertical: salon, medspa, fitness, medical, wellness
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class BusinessUpdate(BaseModel):
    """Business update schema."""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    config_yaml: Optional[str] = None
    features_enabled: Optional[dict] = None


class Business(BaseModel):
    """Business response schema."""
    id: str
    name: str
    type: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    config_yaml: Optional[str] = None
    features_enabled: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
