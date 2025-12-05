"""SMS Campaigns API endpoints for V2 (Mock)."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories import campaign_repo, customer_repo
from app.models.campaign import Campaign, CampaignCreate, CampaignUpdate, CampaignSendResult

router = APIRouter(prefix="/admin", tags=["Campaigns"])


@router.get("/{business_id}/campaigns", response_model=list[Campaign])
async def list_campaigns(
    business_id: str,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List SMS campaigns for a business."""
    return campaign_repo.find_by_business(business_id, status, limit)


@router.get("/{business_id}/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(business_id: str, campaign_id: str):
    """Get a specific campaign."""
    campaign = campaign_repo.find_by_id_and_business(campaign_id, business_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{business_id}/campaigns", response_model=Campaign)
async def create_campaign(business_id: str, data: CampaignCreate):
    """Create a new SMS campaign."""
    recipient_count = customer_repo.count_with_phone(
        business_id, data.recipient_filter.model_dump()
    )
    return campaign_repo.create(business_id, data, recipient_count)


@router.put("/{business_id}/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(business_id: str, campaign_id: str, data: CampaignUpdate):
    """Update a campaign."""
    status = campaign_repo.get_status(business_id, campaign_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if status not in ['draft', 'scheduled']:
        raise HTTPException(status_code=400, detail="Cannot edit sent campaigns")
    
    recipient_count = None
    if data.recipient_filter is not None:
        recipient_count = customer_repo.count_with_phone(
            business_id, data.recipient_filter.model_dump()
        )
    
    campaign = campaign_repo.update(business_id, campaign_id, data, recipient_count)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign


@router.delete("/{business_id}/campaigns/{campaign_id}")
async def delete_campaign(business_id: str, campaign_id: str):
    """Delete a campaign."""
    status = campaign_repo.get_status(business_id, campaign_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if status == 'sent':
        raise HTTPException(status_code=400, detail="Cannot delete sent campaigns")
    
    campaign_repo.delete_by_id_and_business(campaign_id, business_id)
    return {"message": "Campaign deleted"}


@router.post("/{business_id}/campaigns/{campaign_id}/send", response_model=CampaignSendResult)
async def send_campaign(business_id: str, campaign_id: str):
    """Send a campaign (MOCK - no actual SMS sent)."""
    campaign = campaign_repo.find_by_id_and_business(campaign_id, business_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == 'sent':
        raise HTTPException(status_code=400, detail="Campaign already sent")
    
    recipient_count = campaign.recipient_count
    delivered = int(recipient_count * 0.95)
    failed = recipient_count - delivered
    
    campaign_repo.mark_sent(campaign_id)
    
    return CampaignSendResult(
        campaign_id=campaign_id,
        status="sent",
        recipient_count=recipient_count,
        delivered=delivered,
        failed=failed,
        message=f"Campaign sent successfully to {delivered} recipients ({failed} failed)"
    )


@router.get("/{business_id}/campaigns/{campaign_id}/preview")
async def preview_recipients(business_id: str, campaign_id: str, limit: int = Query(default=10, le=50)):
    """Preview recipients for a campaign."""
    recipient_filter = campaign_repo.get_recipient_filter(business_id, campaign_id)
    if recipient_filter is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    total = customer_repo.count_with_phone(business_id, recipient_filter)
    
    recipient_filter_with_limit = recipient_filter.copy()
    customers = customer_repo.get_with_phone(business_id, recipient_filter)[:limit]
    
    return {
        "total": total,
        "preview": [
            {
                "id": c["id"],
                "name": f"{c['first_name']} {c['last_name'] or ''}".strip(),
                "phone": c["phone"]
            }
            for c in customers if c["phone"]
        ]
    }
