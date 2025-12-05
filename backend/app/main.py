"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.db.database import init_db
from app.api import (
    chat_router, auth_router, business_router, admin_router,
    appointments_router, leads_router, customers_router, campaigns_router,
    faqs_router
)
# V3 Routers
from app.api.analytics import router as analytics_router
from app.api.workflows import router as workflows_router
from app.api.conversations import router as conversations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()
    yield


app = FastAPI(
    title="AI Receptionist API",
    description="Keystone AI Receptionist - Backend API for self-care business chatbot",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# V1 Routers
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(admin_router)
app.include_router(chat_router)

# V2 Routers
app.include_router(appointments_router)
app.include_router(leads_router)
app.include_router(customers_router)
app.include_router(campaigns_router)
app.include_router(faqs_router)

# V3 Routers
app.include_router(analytics_router)
app.include_router(workflows_router)
app.include_router(conversations_router)

# Serve static files (chat widget)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Receptionist API",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
