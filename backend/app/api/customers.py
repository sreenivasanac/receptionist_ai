"""Customers API endpoints for V2."""
import uuid
import json
import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File

from app.db.database import get_db_connection
from app.models.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/admin", tags=["Customers"])


@router.get("/{business_id}/customers", response_model=list[Customer])
async def list_customers(
    business_id: str,
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0)
):
    """List customers for a business with optional search."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT c.*, s.name as favorite_service_name
            FROM customers c
            LEFT JOIN services s ON c.favorite_service_id = s.id
            WHERE c.business_id = ?
        """
        params = [business_id]
        
        if search:
            query += """ AND (
                c.first_name LIKE ? OR 
                c.last_name LIKE ? OR 
                c.email LIKE ? OR 
                c.phone LIKE ?
            )"""
            search_param = f"%{search}%"
            params.extend([search_param] * 4)
        
        query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            Customer(
                id=row["id"],
                business_id=row["business_id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                email=row["email"],
                phone=row["phone"],
                visit_count=row["visit_count"],
                last_visit_date=row["last_visit_date"],
                favorite_service_id=row["favorite_service_id"],
                favorite_service_name=row["favorite_service_name"],
                notes=row["notes"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


@router.get("/{business_id}/customers/count")
async def get_customer_count(business_id: str):
    """Get total customer count."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM customers WHERE business_id = ?",
            (business_id,)
        )
        return {"count": cursor.fetchone()["count"]}


@router.get("/{business_id}/customers/{customer_id}", response_model=Customer)
async def get_customer(business_id: str, customer_id: str):
    """Get a specific customer."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, s.name as favorite_service_name
            FROM customers c
            LEFT JOIN services s ON c.favorite_service_id = s.id
            WHERE c.id = ? AND c.business_id = ?
        """, (customer_id, business_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return Customer(
            id=row["id"],
            business_id=row["business_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            visit_count=row["visit_count"],
            last_visit_date=row["last_visit_date"],
            favorite_service_id=row["favorite_service_id"],
            favorite_service_name=row["favorite_service_name"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


@router.post("/{business_id}/customers", response_model=Customer)
async def create_customer(business_id: str, data: CustomerCreate):
    """Create a new customer."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check for duplicate email/phone
        if data.email:
            cursor.execute(
                "SELECT id FROM customers WHERE business_id = ? AND email = ?",
                (business_id, data.email)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Customer with this email already exists")
        
        if data.phone:
            cursor.execute(
                "SELECT id FROM customers WHERE business_id = ? AND phone = ?",
                (business_id, data.phone)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Customer with this phone already exists")
        
        customer_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO customers 
            (id, business_id, first_name, last_name, email, phone, notes, visit_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (customer_id, business_id, data.first_name, data.last_name, 
              data.email, data.phone, data.notes, now, now))
        conn.commit()
        
        return await get_customer(business_id, customer_id)


@router.put("/{business_id}/customers/{customer_id}", response_model=Customer)
async def update_customer(business_id: str, customer_id: str, data: CustomerUpdate):
    """Update a customer."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if data.first_name is not None:
            updates.append("first_name = ?")
            params.append(data.first_name)
        if data.last_name is not None:
            updates.append("last_name = ?")
            params.append(data.last_name)
        if data.email is not None:
            updates.append("email = ?")
            params.append(data.email)
        if data.phone is not None:
            updates.append("phone = ?")
            params.append(data.phone)
        if data.notes is not None:
            updates.append("notes = ?")
            params.append(data.notes)
        
        if not updates:
            return await get_customer(business_id, customer_id)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([customer_id, business_id])
        
        cursor.execute(f"""
            UPDATE customers SET {', '.join(updates)}
            WHERE id = ? AND business_id = ?
        """, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return await get_customer(business_id, customer_id)


@router.delete("/{business_id}/customers/{customer_id}")
async def delete_customer(business_id: str, customer_id: str):
    """Delete a customer."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM customers WHERE id = ? AND business_id = ?",
            (customer_id, business_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {"message": "Customer deleted"}


@router.post("/{business_id}/customers/import")
async def import_customers_csv(business_id: str, file: UploadFile = File(...)):
    """
    Import customers from CSV file.
    Expected columns: first_name, last_name, email, mobile_number
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    skipped = 0
    errors = []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        for i, row in enumerate(reader, start=2):  # Start at 2 to account for header
            try:
                first_name = row.get('first_name', '').strip()
                if not first_name:
                    skipped += 1
                    continue
                
                last_name = row.get('last_name', '').strip() or None
                email = row.get('email', '').strip() or None
                phone = row.get('mobile_number', '').strip() or None
                
                # Skip if no contact info
                if not email and not phone:
                    skipped += 1
                    continue
                
                # Check for existing customer
                existing = None
                if email:
                    cursor.execute(
                        "SELECT id FROM customers WHERE business_id = ? AND email = ?",
                        (business_id, email)
                    )
                    existing = cursor.fetchone()
                
                if not existing and phone:
                    cursor.execute(
                        "SELECT id FROM customers WHERE business_id = ? AND phone = ?",
                        (business_id, phone)
                    )
                    existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute("""
                        UPDATE customers SET 
                            first_name = ?, last_name = COALESCE(?, last_name),
                            email = COALESCE(?, email), phone = COALESCE(?, phone),
                            updated_at = ?
                        WHERE id = ?
                    """, (first_name, last_name, email, phone, now, existing['id']))
                else:
                    # Create new
                    customer_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO customers 
                        (id, business_id, first_name, last_name, email, phone, visit_count, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    """, (customer_id, business_id, first_name, last_name, email, phone, now, now))
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
        
        conn.commit()
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10]  # Return first 10 errors
    }
