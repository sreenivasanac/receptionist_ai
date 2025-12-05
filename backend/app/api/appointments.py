"""Appointments API endpoints for V2."""
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_db_connection
from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate

router = APIRouter(prefix="/admin", tags=["Appointments"])


@router.get("/{business_id}/appointments", response_model=list[Appointment])
async def list_appointments(
    business_id: str,
    status: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List appointments for a business with optional filters."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT a.*, s.name as service_name, st.name as staff_name
            FROM appointments a
            LEFT JOIN services s ON a.service_id = s.id
            LEFT JOIN staff st ON a.staff_id = st.id
            WHERE a.business_id = ?
        """
        params = [business_id]
        
        if status:
            query += " AND a.status = ?"
            params.append(status)
        
        if date_from:
            query += " AND a.date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND a.date <= ?"
            params.append(date_to)
        
        query += " ORDER BY a.date DESC, a.time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            Appointment(
                id=row["id"],
                business_id=row["business_id"],
                customer_id=row["customer_id"],
                service_id=row["service_id"],
                staff_id=row["staff_id"],
                customer_name=row["customer_name"],
                customer_phone=row["customer_phone"],
                customer_email=row["customer_email"],
                date=row["date"],
                time=row["time"],
                duration_minutes=row["duration_minutes"],
                status=row["status"],
                notes=row["notes"],
                service_name=row["service_name"],
                staff_name=row["staff_name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


@router.get("/{business_id}/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(business_id: str, appointment_id: str):
    """Get a specific appointment."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, s.name as service_name, st.name as staff_name
            FROM appointments a
            LEFT JOIN services s ON a.service_id = s.id
            LEFT JOIN staff st ON a.staff_id = st.id
            WHERE a.id = ? AND a.business_id = ?
        """, (appointment_id, business_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return Appointment(
            id=row["id"],
            business_id=row["business_id"],
            customer_id=row["customer_id"],
            service_id=row["service_id"],
            staff_id=row["staff_id"],
            customer_name=row["customer_name"],
            customer_phone=row["customer_phone"],
            customer_email=row["customer_email"],
            date=row["date"],
            time=row["time"],
            duration_minutes=row["duration_minutes"],
            status=row["status"],
            notes=row["notes"],
            service_name=row["service_name"],
            staff_name=row["staff_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.post("/{business_id}/appointments", response_model=Appointment)
async def create_appointment(business_id: str, data: AppointmentCreate):
    """Create a new appointment (admin booking)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        appointment_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO appointments 
            (id, business_id, customer_id, service_id, staff_id, customer_name,
             customer_phone, customer_email, date, time, duration_minutes,
             status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
        """, (
            appointment_id, business_id, data.customer_id, data.service_id,
            data.staff_id, data.customer_name, data.customer_phone,
            data.customer_email, data.date, data.time, data.duration_minutes,
            data.notes, now, now
        ))
        conn.commit()
        
        return await get_appointment(business_id, appointment_id)


@router.put("/{business_id}/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(business_id: str, appointment_id: str, data: AppointmentUpdate):
    """Update an appointment."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build update query
        updates = []
        params = []
        
        if data.service_id is not None:
            updates.append("service_id = ?")
            params.append(data.service_id)
        if data.date is not None:
            updates.append("date = ?")
            params.append(data.date)
        if data.time is not None:
            updates.append("time = ?")
            params.append(data.time)
        if data.duration_minutes is not None:
            updates.append("duration_minutes = ?")
            params.append(data.duration_minutes)
        if data.staff_id is not None:
            updates.append("staff_id = ?")
            params.append(data.staff_id)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        if data.notes is not None:
            updates.append("notes = ?")
            params.append(data.notes)
        
        if not updates:
            return await get_appointment(business_id, appointment_id)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([appointment_id, business_id])
        
        cursor.execute(f"""
            UPDATE appointments SET {', '.join(updates)}
            WHERE id = ? AND business_id = ?
        """, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return await get_appointment(business_id, appointment_id)


@router.delete("/{business_id}/appointments/{appointment_id}")
async def delete_appointment(business_id: str, appointment_id: str):
    """Delete an appointment."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM appointments WHERE id = ? AND business_id = ?",
            (appointment_id, business_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {"message": "Appointment deleted"}


@router.post("/{business_id}/appointments/{appointment_id}/status")
async def update_appointment_status(business_id: str, appointment_id: str, status: str):
    """Update appointment status (shortcut endpoint)."""
    valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments SET status = ?, updated_at = ?
            WHERE id = ? AND business_id = ?
        """, (status, datetime.now().isoformat(), appointment_id, business_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {"appointment_id": appointment_id, "status": status}
