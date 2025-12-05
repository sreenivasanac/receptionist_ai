"""API route handlers."""
# V1 Routers
from .chat import router as chat_router
from .auth import router as auth_router
from .business import router as business_router
from .admin import router as admin_router

# V2 Routers
from .appointments import router as appointments_router
from .leads import router as leads_router
from .customers import router as customers_router
from .campaigns import router as campaigns_router
from .faqs import router as faqs_router

__all__ = [
    # V1
    "chat_router", 
    "auth_router", 
    "business_router", 
    "admin_router",
    # V2
    "appointments_router",
    "leads_router",
    "customers_router",
    "campaigns_router",
    "faqs_router",
]
