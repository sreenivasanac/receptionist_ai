"""SMS Campaigns API endpoints for V2 (Mock)."""
import uuid
import json
from datetime import datetime
from typing import Optional
import random

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_db_connection
from app.models.campaign import Campaign, CampaignCreate, CampaignUpdate, CampaignSendResult

router = APIRouter(prefix="/admin", tags=["Campaigns"])


@router.get("/{business_id}/campaigns", response_model=list[Campaign])
async def list_campaigns(
    business_id: str,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List SMS campaigns for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM sms_campaigns WHERE business_id = ?"
        params = [business_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            Campaign(
                id=row["id"],
                business_id=row["business_id"],
                name=row["name"],
                message=row["message"],
                recipient_filter=json.loads(row["recipient_filter"] or "{}"),
                recipient_count=row["recipient_count"],
                status=row["status"],
                scheduled_at=row["scheduled_at"],
                sent_at=row["sent_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


@router.get("/{business_id}/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(business_id: str, campaign_id: str):
    """Get a specific campaign."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return Campaign(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            message=row["message"],
            recipient_filter=json.loads(row["recipient_filter"] or "{}"),
            recipient_count=row["recipient_count"],
            status=row["status"],
            scheduled_at=row["scheduled_at"],
            sent_at=row["sent_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.post("/{business_id}/campaigns", response_model=Campaign)
async def create_campaign(business_id: str, data: CampaignCreate):
    """Create a new SMS campaign."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Calculate recipient count based on filter
        recipient_count = _calculate_recipients(cursor, business_id, data.recipient_filter.model_dump())
        
        campaign_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO sms_campaigns 
            (id, business_id, name, message, recipient_filter, recipient_count, status, scheduled_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
        """, (
            campaign_id, business_id, data.name, data.message,
            json.dumps(data.recipient_filter.model_dump()), recipient_count,
            data.scheduled_at, now, now
        ))
        conn.commit()
        
        return await get_campaign(business_id, campaign_id)


@router.put("/{business_id}/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(business_id: str, campaign_id: str, data: CampaignUpdate):
    """Update a campaign."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if campaign exists and is editable
        cursor.execute(
            "SELECT status FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if existing["status"] not in ['draft', 'scheduled']:
            raise HTTPException(status_code=400, detail="Cannot edit sent campaigns")
        
        updates = []
        params = []
        
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.message is not None:
            updates.append("message = ?")
            params.append(data.message)
        if data.recipient_filter is not None:
            updates.append("recipient_filter = ?")
            params.append(json.dumps(data.recipient_filter.model_dump()))
            # Recalculate recipient count
            recipient_count = _calculate_recipients(cursor, business_id, data.recipient_filter.model_dump())
            updates.append("recipient_count = ?")
            params.append(recipient_count)
        if data.scheduled_at is not None:
            updates.append("scheduled_at = ?")
            params.append(data.scheduled_at)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        
        if not updates:
            return await get_campaign(business_id, campaign_id)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([campaign_id, business_id])
        
        cursor.execute(f"""
            UPDATE sms_campaigns SET {', '.join(updates)}
            WHERE id = ? AND business_id = ?
        """, params)
        conn.commit()
        
        return await get_campaign(business_id, campaign_id)


@router.delete("/{business_id}/campaigns/{campaign_id}")
async def delete_campaign(business_id: str, campaign_id: str):
    """Delete a campaign."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check status
        cursor.execute(
            "SELECT status FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if existing["status"] == 'sent':
            raise HTTPException(status_code=400, detail="Cannot delete sent campaigns")
        
        cursor.execute(
            "DELETE FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        conn.commit()
        
        return {"message": "Campaign deleted"}


@router.post("/{business_id}/campaigns/{campaign_id}/send", response_model=CampaignSendResult)
async def send_campaign(business_id: str, campaign_id: str):
    """
    Send a campaign (MOCK - no actual SMS sent).
    This simulates sending and updates the campaign status.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        campaign = cursor.fetchone()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if campaign["status"] == 'sent':
            raise HTTPException(status_code=400, detail="Campaign already sent")
        
        recipient_count = campaign["recipient_count"]
        
        # Simulate sending with mock success/failure rates
        delivered = int(recipient_count * 0.95)  # 95% delivery rate
        failed = recipient_count - delivered
        
        # Update campaign status
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE sms_campaigns SET status = 'sent', sent_at = ?, updated_at = ?
            WHERE id = ?
        """, (now, now, campaign_id))
        conn.commit()
        
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
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT recipient_filter FROM sms_campaigns WHERE id = ? AND business_id = ?",
            (campaign_id, business_id)
        )
        campaign = cursor.fetchone()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        filter_data = json.loads(campaign["recipient_filter"] or "{}")
        query, params = _build_recipient_query(business_id, filter_data)
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        recipients = cursor.fetchall()
        
        return {
            "total": _calculate_recipients(cursor, business_id, filter_data),
            "preview": [
                {
                    "id": r["id"],
                    "name": f"{r['first_name']} {r['last_name'] or ''}".strip(),
                    "phone": r["phone"]
                }
                for r in recipients if r["phone"]
            ]
        }


def _build_recipient_query(business_id: str, filter_data: dict) -> tuple[str, list]:
    """Build SQL query for recipient filtering."""
    query = "SELECT * FROM customers WHERE business_id = ? AND phone IS NOT NULL"
    params = [business_id]
    
    if filter_data.get("custom_ids"):
        placeholders = ",".join(["?" for _ in filter_data["custom_ids"]])
        query += f" AND id IN ({placeholders})"
        params.extend(filter_data["custom_ids"])
    elif not filter_data.get("all_customers"):
        if filter_data.get("visit_count_min"):
            query += " AND visit_count >= ?"
            params.append(filter_data["visit_count_min"])
        if filter_data.get("visit_count_max"):
            query += " AND visit_count <= ?"
            params.append(filter_data["visit_count_max"])
        if filter_data.get("favorite_service_id"):
            query += " AND favorite_service_id = ?"
            params.append(filter_data["favorite_service_id"])
    
    return query, params


def _calculate_recipients(cursor, business_id: str, filter_data: dict) -> int:
    """Calculate number of recipients based on filter."""
    query, params = _build_recipient_query(business_id, filter_data)
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
    cursor.execute(count_query, params)
    return cursor.fetchone()["count"]
