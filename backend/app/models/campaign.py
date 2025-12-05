"""SMS Campaign models for V2."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


CampaignStatus = Literal['draft', 'scheduled', 'sending', 'sent', 'failed']


class RecipientFilter(BaseModel):
    """Filter criteria for SMS recipients."""
    all_customers: bool = False
    visit_count_min: Optional[int] = None
    visit_count_max: Optional[int] = None
    last_visit_days_ago: Optional[int] = None
    favorite_service_id: Optional[str] = None
    custom_ids: Optional[list[str]] = None


class CampaignBase(BaseModel):
    """Base campaign fields."""
    name: Optional[str] = None
    message: str
    recipient_filter: RecipientFilter = Field(default_factory=RecipientFilter)


class CampaignCreate(CampaignBase):
    """Create campaign request."""
    scheduled_at: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Update campaign request."""
    name: Optional[str] = None
    message: Optional[str] = None
    recipient_filter: Optional[RecipientFilter] = None
    status: Optional[CampaignStatus] = None
    scheduled_at: Optional[str] = None


class Campaign(BaseModel):
    """Full campaign model."""
    id: str
    business_id: str
    name: Optional[str] = None
    message: str
    recipient_filter: dict = Field(default_factory=dict)
    recipient_count: int = 0
    status: CampaignStatus = 'draft'
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CampaignSendResult(BaseModel):
    """Campaign send result (mock)."""
    campaign_id: str
    status: str
    recipient_count: int
    message: str
    # Mock delivery stats
    delivered: int = 0
    failed: int = 0
