"""Leads API endpoints for V2."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories import lead_repo, waitlist_repo, service_repo
from app.models.lead import Lead, LeadCreate, LeadUpdate, WaitlistEntry, WaitlistUpdate

router = APIRouter(prefix="/admin", tags=["Leads"])


# ============ LEADS ENDPOINTS ============

@router.get("/{business_id}/leads", response_model=list[Lead])
async def list_leads(
    business_id: str,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List leads for a business."""
    return lead_repo.find_by_business(business_id, status, limit)


@router.get("/{business_id}/leads/{lead_id}", response_model=Lead)
async def get_lead(business_id: str, lead_id: str):
    """Get a specific lead."""
    lead = lead_repo.find_by_id_and_business(lead_id, business_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/{business_id}/leads", response_model=Lead)
async def create_lead(business_id: str, data: LeadCreate):
    """Create a new lead."""
    return lead_repo.create(business_id, data)


@router.put("/{business_id}/leads/{lead_id}", response_model=Lead)
async def update_lead(business_id: str, lead_id: str, data: LeadUpdate):
    """Update a lead."""
    lead = lead_repo.update(business_id, lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{business_id}/leads/{lead_id}")
async def delete_lead(business_id: str, lead_id: str):
    """Delete a lead."""
    if not lead_repo.delete_by_id_and_business(lead_id, business_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


@router.post("/{business_id}/leads/{lead_id}/status")
async def update_lead_status(business_id: str, lead_id: str, status: str):
    """Update lead status."""
    valid_statuses = ['new', 'contacted', 'qualified', 'converted', 'lost']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    if not lead_repo.update_status(business_id, lead_id, status):
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"lead_id": lead_id, "status": status}


# ============ WAITLIST ENDPOINTS ============

@router.get("/{business_id}/waitlist", response_model=list[WaitlistEntry])
async def list_waitlist(
    business_id: str,
    status: Optional[str] = Query(default="waiting"),
    limit: int = Query(default=50, le=100)
):
    """List waitlist entries for a business."""
    return waitlist_repo.find_by_business(business_id, status, limit)


@router.put("/{business_id}/waitlist/{waitlist_id}", response_model=WaitlistEntry)
async def update_waitlist_entry(business_id: str, waitlist_id: str, data: WaitlistUpdate):
    """Update a waitlist entry."""
    entry = waitlist_repo.update(business_id, waitlist_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    return entry


@router.delete("/{business_id}/waitlist/{waitlist_id}")
async def delete_waitlist_entry(business_id: str, waitlist_id: str):
    """Delete a waitlist entry."""
    if not waitlist_repo.delete_by_id_and_business(waitlist_id, business_id):
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    return {"message": "Waitlist entry deleted"}
