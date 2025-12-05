"""Customer models for V2."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Base customer fields."""
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Create customer request."""
    pass


class CustomerUpdate(BaseModel):
    """Update customer request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class Customer(CustomerBase):
    """Full customer model."""
    id: str
    business_id: str
    visit_count: int = 0
    last_visit_date: Optional[str] = None
    favorite_service_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Joined fields for display
    favorite_service_name: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class CustomerIdentification(BaseModel):
    """Customer identification response."""
    customer_id: Optional[str] = None
    name: Optional[str] = None
    is_returning: bool = False
    visit_count: int = 0
    last_visit: Optional[dict] = None  # {date, service}
    message: str


class CustomerVisit(BaseModel):
    """Customer visit history entry."""
    date: str
    service: str
    service_id: str
    staff_name: Optional[str] = None
    notes: Optional[str] = None


class CustomerHistory(BaseModel):
    """Customer visit history response."""
    customer_id: str
    name: str
    visits: list[CustomerVisit] = Field(default_factory=list)
    total_visits: int = 0
    favorite_service: Optional[str] = None
    average_visit_frequency_days: Optional[int] = None


class CustomerCSVRow(BaseModel):
    """CSV import row format."""
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
