"""Leads API endpoints for V2."""
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_db_connection
from app.models.lead import Lead, LeadCreate, LeadUpdate, WaitlistEntry, WaitlistCreate, WaitlistUpdate

router = APIRouter(prefix="/admin", tags=["Leads"])


# ============ LEADS ENDPOINTS ============

@router.get("/{business_id}/leads", response_model=list[Lead])
async def list_leads(
    business_id: str,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List leads for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM leads WHERE business_id = ?"
        params = [business_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            Lead(
                id=row["id"],
                business_id=row["business_id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                interest=row["interest"],
                notes=row["notes"],
                company=row["company"],
                status=row["status"],
                source=row["source"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


@router.get("/{business_id}/leads/{lead_id}", response_model=Lead)
async def get_lead(business_id: str, lead_id: str):
    """Get a specific lead."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM leads WHERE id = ? AND business_id = ?",
            (lead_id, business_id)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return Lead(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            interest=row["interest"],
            notes=row["notes"],
            company=row["company"],
            status=row["status"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.post("/{business_id}/leads", response_model=Lead)
async def create_lead(business_id: str, data: LeadCreate):
    """Create a new lead."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        lead_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO leads 
            (id, business_id, name, email, phone, interest, notes, company, source, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
        """, (lead_id, business_id, data.name, data.email, data.phone, 
              data.interest, data.notes, data.company, data.source, now, now))
        conn.commit()
        
        return await get_lead(business_id, lead_id)


@router.put("/{business_id}/leads/{lead_id}", response_model=Lead)
async def update_lead(business_id: str, lead_id: str, data: LeadUpdate):
    """Update a lead."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.email is not None:
            updates.append("email = ?")
            params.append(data.email)
        if data.phone is not None:
            updates.append("phone = ?")
            params.append(data.phone)
        if data.interest is not None:
            updates.append("interest = ?")
            params.append(data.interest)
        if data.notes is not None:
            updates.append("notes = ?")
            params.append(data.notes)
        if data.company is not None:
            updates.append("company = ?")
            params.append(data.company)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        
        if not updates:
            return await get_lead(business_id, lead_id)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([lead_id, business_id])
        
        cursor.execute(f"""
            UPDATE leads SET {', '.join(updates)}
            WHERE id = ? AND business_id = ?
        """, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return await get_lead(business_id, lead_id)


@router.delete("/{business_id}/leads/{lead_id}")
async def delete_lead(business_id: str, lead_id: str):
    """Delete a lead."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM leads WHERE id = ? AND business_id = ?",
            (lead_id, business_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {"message": "Lead deleted"}


@router.post("/{business_id}/leads/{lead_id}/status")
async def update_lead_status(business_id: str, lead_id: str, status: str):
    """Update lead status."""
    valid_statuses = ['new', 'contacted', 'qualified', 'converted', 'lost']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leads SET status = ?, updated_at = ?
            WHERE id = ? AND business_id = ?
        """, (status, datetime.now().isoformat(), lead_id, business_id))
        conn.commit()
        
        if cursor.rowcount == 0:
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
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT w.*, s.name as service_name
            FROM waitlist w
            LEFT JOIN services s ON w.service_id = s.id
            WHERE w.business_id = ?
        """
        params = [business_id]
        
        if status:
            query += " AND w.status = ?"
            params.append(status)
        
        query += " ORDER BY w.created_at ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            WaitlistEntry(
                id=row["id"],
                business_id=row["business_id"],
                customer_id=row["customer_id"],
                service_id=row["service_id"],
                customer_name=row["customer_name"],
                customer_contact=row["customer_contact"],
                preferred_dates=json.loads(row["preferred_dates"] or "[]"),
                preferred_times=json.loads(row["preferred_times"] or "[]"),
                contact_method=row["contact_method"],
                status=row["status"],
                notes=row["notes"],
                service_name=row["service_name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


@router.put("/{business_id}/waitlist/{waitlist_id}", response_model=WaitlistEntry)
async def update_waitlist_entry(business_id: str, waitlist_id: str, data: WaitlistUpdate):
    """Update a waitlist entry."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if data.preferred_dates is not None:
            updates.append("preferred_dates = ?")
            params.append(json.dumps(data.preferred_dates))
        if data.preferred_times is not None:
            updates.append("preferred_times = ?")
            params.append(json.dumps(data.preferred_times))
        if data.contact_method is not None:
            updates.append("contact_method = ?")
            params.append(data.contact_method)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        if data.notes is not None:
            updates.append("notes = ?")
            params.append(data.notes)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([waitlist_id, business_id])
        
        cursor.execute(f"""
            UPDATE waitlist SET {', '.join(updates)}
            WHERE id = ? AND business_id = ?
        """, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Waitlist entry not found")
        
        # Get updated entry
        cursor.execute("""
            SELECT w.*, s.name as service_name
            FROM waitlist w
            LEFT JOIN services s ON w.service_id = s.id
            WHERE w.id = ? AND w.business_id = ?
        """, (waitlist_id, business_id))
        row = cursor.fetchone()
        
        return WaitlistEntry(
            id=row["id"],
            business_id=row["business_id"],
            customer_id=row["customer_id"],
            service_id=row["service_id"],
            customer_name=row["customer_name"],
            customer_contact=row["customer_contact"],
            preferred_dates=json.loads(row["preferred_dates"] or "[]"),
            preferred_times=json.loads(row["preferred_times"] or "[]"),
            contact_method=row["contact_method"],
            status=row["status"],
            notes=row["notes"],
            service_name=row["service_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.delete("/{business_id}/waitlist/{waitlist_id}")
async def delete_waitlist_entry(business_id: str, waitlist_id: str):
    """Delete a waitlist entry."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM waitlist WHERE id = ? AND business_id = ?",
            (waitlist_id, business_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Waitlist entry not found")
        
        return {"message": "Waitlist entry deleted"}
