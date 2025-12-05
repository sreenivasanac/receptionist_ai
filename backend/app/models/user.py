"""User models."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class UserCreate(BaseModel):
    """User registration schema."""
    username: str
    email: Optional[str] = None
    role: Literal["admin", "business_owner"]
    business_name: Optional[str] = None
    business_type: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema."""
    username: str
    role: Literal["admin", "business_owner"]


class User(BaseModel):
    """User response schema."""
    id: str
    username: str
    email: Optional[str] = None
    role: str
    business_id: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
