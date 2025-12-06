"""Pydantic models for LLM-extracted business configuration."""
from typing import Optional
from pydantic import BaseModel, Field


class ExtractedHours(BaseModel):
    """Business hours for a single day."""
    open: Optional[str] = Field(None, description="Opening time in HH:MM format (24-hour)")
    close: Optional[str] = Field(None, description="Closing time in HH:MM format (24-hour)")
    closed: bool = Field(False, description="Whether the business is closed on this day")


class ExtractedService(BaseModel):
    """A service offered by the business."""
    name: str = Field(..., description="Name of the service")
    description: Optional[str] = Field(None, description="Description of the service")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    price: Optional[float] = Field(None, description="Price in dollars")


class ExtractedPolicies(BaseModel):
    """Business policies."""
    cancellation: Optional[str] = Field(None, description="Cancellation policy")
    walk_ins: Optional[str] = Field(None, description="Walk-in policy")
    deposit: Optional[bool] = Field(None, description="Whether deposit is required")
    deposit_amount: Optional[float] = Field(None, description="Deposit amount if required")


class ExtractedFAQ(BaseModel):
    """A frequently asked question and answer."""
    question: str = Field(..., description="The question")
    answer: str = Field(..., description="The answer")


class ExtractedBusinessConfig(BaseModel):
    """Structured output model for OpenAI extraction of business information."""
    name: Optional[str] = Field(None, description="Business name")
    location: Optional[str] = Field(None, description="Full business address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    hours: Optional[dict[str, ExtractedHours]] = Field(
        None, 
        description="Business hours by day (monday, tuesday, etc.)"
    )
    services: Optional[list[ExtractedService]] = Field(
        None, 
        description="List of services offered"
    )
    policies: Optional[ExtractedPolicies] = Field(
        None, 
        description="Business policies"
    )
    faqs: Optional[list[ExtractedFAQ]] = Field(
        None, 
        description="Frequently asked questions"
    )
