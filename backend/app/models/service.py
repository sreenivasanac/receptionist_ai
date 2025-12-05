"""Service models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ServiceCreate(BaseModel):
    """Service creation schema."""
    name: str
    description: Optional[str] = None
    duration_minutes: int = 30
    price: float = 0
    requires_consultation: bool = False


class Service(BaseModel):
    """Service response schema."""
    id: str
    business_id: str
    name: str
    description: Optional[str] = None
    duration_minutes: int = 30
    price: float = 0
    requires_consultation: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
