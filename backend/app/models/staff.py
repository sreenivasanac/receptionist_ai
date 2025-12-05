"""Staff models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StaffCreate(BaseModel):
    """Staff creation schema."""
    name: str
    role_title: Optional[str] = None
    services_offered: list[str] = Field(default_factory=list)


class Staff(BaseModel):
    """Staff response schema."""
    id: str
    business_id: str
    name: str
    role_title: Optional[str] = None
    services_offered: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
