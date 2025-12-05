"""Admin panel API endpoints for staff and service management."""
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.database import get_db_connection
from app.models.service import Service, ServiceCreate
from app.models.staff import Staff, StaffCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============ STAFF ENDPOINTS ============

@router.get("/{business_id}/staff", response_model=list[Staff])
async def list_staff(business_id: str, active_only: bool = Query(default=True)):
    """List all staff members for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM staff WHERE business_id = ?"
        params = [business_id]
        
        if active_only:
            query += " AND is_active = 1"
        
        cursor.execute(query, params)
        staff_rows = cursor.fetchall()
        
        return [
            Staff(
                id=row["id"],
                business_id=row["business_id"],
                name=row["name"],
                role_title=row["role_title"],
                services_offered=json.loads(row["services_offered"] or "[]"),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in staff_rows
        ]


@router.post("/{business_id}/staff", response_model=Staff)
async def create_staff(business_id: str, staff_data: StaffCreate):
    """Create a new staff member."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
        staff_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO staff (id, business_id, name, role_title, services_offered, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            staff_id,
            business_id,
            staff_data.name,
            staff_data.role_title,
            json.dumps(staff_data.services_offered),
            now,
            now
        ))
        conn.commit()
        
        return Staff(
            id=staff_id,
            business_id=business_id,
            name=staff_data.name,
            role_title=staff_data.role_title,
            services_offered=staff_data.services_offered,
            is_active=True,
            created_at=now,
            updated_at=now
        )


@router.get("/{business_id}/staff/{staff_id}", response_model=Staff)
async def get_staff(business_id: str, staff_id: str):
    """Get a specific staff member."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM staff WHERE id = ? AND business_id = ?",
            (staff_id, business_id)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return Staff(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            role_title=row["role_title"],
            services_offered=json.loads(row["services_offered"] or "[]"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.put("/{business_id}/staff/{staff_id}", response_model=Staff)
async def update_staff(business_id: str, staff_id: str, staff_data: StaffCreate):
    """Update a staff member."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM staff WHERE id = ? AND business_id = ?",
            (staff_id, business_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE staff 
            SET name = ?, role_title = ?, services_offered = ?, updated_at = ?
            WHERE id = ? AND business_id = ?
        """, (
            staff_data.name,
            staff_data.role_title,
            json.dumps(staff_data.services_offered),
            now,
            staff_id,
            business_id
        ))
        conn.commit()
        
        return await get_staff(business_id, staff_id)


@router.delete("/{business_id}/staff/{staff_id}")
async def delete_staff(business_id: str, staff_id: str, hard_delete: bool = Query(default=False)):
    """Delete (or deactivate) a staff member."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM staff WHERE id = ? AND business_id = ?",
            (staff_id, business_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        if hard_delete:
            cursor.execute(
                "DELETE FROM staff WHERE id = ? AND business_id = ?",
                (staff_id, business_id)
            )
        else:
            cursor.execute(
                "UPDATE staff SET is_active = 0, updated_at = ? WHERE id = ? AND business_id = ?",
                (datetime.now().isoformat(), staff_id, business_id)
            )
        
        conn.commit()
        
        return {"message": "Staff member deleted" if hard_delete else "Staff member deactivated"}


# ============ SERVICES ENDPOINTS ============

@router.get("/{business_id}/services", response_model=list[Service])
async def list_services(business_id: str, active_only: bool = Query(default=True)):
    """List all services for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM services WHERE business_id = ?"
        params = [business_id]
        
        if active_only:
            query += " AND is_active = 1"
        
        cursor.execute(query, params)
        service_rows = cursor.fetchall()
        
        return [
            Service(
                id=row["id"],
                business_id=row["business_id"],
                name=row["name"],
                description=row["description"],
                duration_minutes=row["duration_minutes"],
                price=row["price"],
                requires_consultation=bool(row["requires_consultation"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in service_rows
        ]


@router.post("/{business_id}/services", response_model=Service)
async def create_service(business_id: str, service_data: ServiceCreate):
    """Create a new service."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
        service_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO services (id, business_id, name, description, duration_minutes, price, requires_consultation, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            service_id,
            business_id,
            service_data.name,
            service_data.description,
            service_data.duration_minutes,
            service_data.price,
            1 if service_data.requires_consultation else 0,
            now,
            now
        ))
        conn.commit()
        
        return Service(
            id=service_id,
            business_id=business_id,
            name=service_data.name,
            description=service_data.description,
            duration_minutes=service_data.duration_minutes,
            price=service_data.price,
            requires_consultation=service_data.requires_consultation,
            is_active=True,
            created_at=now,
            updated_at=now
        )


@router.put("/{business_id}/services/{service_id}", response_model=Service)
async def update_service(business_id: str, service_id: str, service_data: ServiceCreate):
    """Update a service."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM services WHERE id = ? AND business_id = ?",
            (service_id, business_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE services 
            SET name = ?, description = ?, duration_minutes = ?, price = ?, requires_consultation = ?, updated_at = ?
            WHERE id = ? AND business_id = ?
        """, (
            service_data.name,
            service_data.description,
            service_data.duration_minutes,
            service_data.price,
            1 if service_data.requires_consultation else 0,
            now,
            service_id,
            business_id
        ))
        conn.commit()
        
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        row = cursor.fetchone()
        
        return Service(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            description=row["description"],
            duration_minutes=row["duration_minutes"],
            price=row["price"],
            requires_consultation=bool(row["requires_consultation"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.delete("/{business_id}/services/{service_id}")
async def delete_service(business_id: str, service_id: str, hard_delete: bool = Query(default=False)):
    """Delete (or deactivate) a service."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM services WHERE id = ? AND business_id = ?",
            (service_id, business_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Service not found")
        
        if hard_delete:
            cursor.execute(
                "DELETE FROM services WHERE id = ? AND business_id = ?",
                (service_id, business_id)
            )
        else:
            cursor.execute(
                "UPDATE services SET is_active = 0, updated_at = ? WHERE id = ? AND business_id = ?",
                (datetime.now().isoformat(), service_id, business_id)
            )
        
        conn.commit()
        
        return {"message": "Service deleted" if hard_delete else "Service deactivated"}
