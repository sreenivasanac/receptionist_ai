"""Analytics API endpoints for V3 dashboard."""
from typing import Optional
from fastapi import APIRouter, Query

from app.repositories import analytics_repo

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary/{business_id}")
async def get_summary(
    business_id: str,
    period: str = Query(default="last_30_days", description="Time period: today, this_week, this_month, last_30_days, last_90_days")
):
    """Get summary analytics for the dashboard."""
    summary = analytics_repo.get_summary(business_id, period)
    return {
        "period": period,
        "summary": summary.model_dump()
    }


@router.get("/leads/{business_id}")
async def get_lead_stats(
    business_id: str,
    period: str = Query(default="last_30_days")
):
    """Get detailed lead statistics."""
    stats = analytics_repo.get_lead_stats(business_id, period)
    return {
        "period": period,
        "stats": stats.model_dump()
    }


@router.get("/appointments/{business_id}")
async def get_appointment_stats(
    business_id: str,
    period: str = Query(default="last_30_days")
):
    """Get detailed appointment statistics."""
    stats = analytics_repo.get_appointment_stats(business_id, period)
    return {
        "period": period,
        "stats": stats.model_dump()
    }


@router.get("/conversations/{business_id}")
async def get_conversation_stats(
    business_id: str,
    period: str = Query(default="last_30_days")
):
    """Get detailed conversation statistics."""
    stats = analytics_repo.get_conversation_stats(business_id, period)
    return {
        "period": period,
        "stats": stats.model_dump()
    }


@router.get("/waitlist/{business_id}")
async def get_waitlist_stats(
    business_id: str,
    period: str = Query(default="last_30_days")
):
    """Get waitlist conversion statistics."""
    stats = analytics_repo.get_waitlist_stats(business_id, period)
    return {
        "period": period,
        "stats": stats
    }


@router.get("/overview/{business_id}")
async def get_overview(
    business_id: str,
    period: str = Query(default="last_30_days")
):
    """Get complete analytics overview for dashboard."""
    summary = analytics_repo.get_summary(business_id, period)
    lead_stats = analytics_repo.get_lead_stats(business_id, period)
    appointment_stats = analytics_repo.get_appointment_stats(business_id, period)
    conversation_stats = analytics_repo.get_conversation_stats(business_id, period)
    waitlist_stats = analytics_repo.get_waitlist_stats(business_id, period)
    
    return {
        "period": period,
        "summary": summary.model_dump(),
        "leads": lead_stats.model_dump(),
        "appointments": appointment_stats.model_dump(),
        "conversations": conversation_stats.model_dump(),
        "waitlist": waitlist_stats
    }
