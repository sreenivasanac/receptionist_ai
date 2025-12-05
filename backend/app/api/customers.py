"""Customers API endpoints for V2."""
import csv
import io
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File

from app.repositories import customer_repo
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
    return customer_repo.find_by_business(business_id, search, limit, offset)


@router.get("/{business_id}/customers/count")
async def get_customer_count(business_id: str):
    """Get total customer count."""
    return {"count": customer_repo.count_by_business(business_id)}


@router.get("/{business_id}/customers/{customer_id}", response_model=Customer)
async def get_customer(business_id: str, customer_id: str):
    """Get a specific customer."""
    customer = customer_repo.find_with_service_name(business_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/{business_id}/customers", response_model=Customer)
async def create_customer(business_id: str, data: CustomerCreate):
    """Create a new customer."""
    if data.email and customer_repo.email_exists(business_id, data.email):
        raise HTTPException(status_code=400, detail="Customer with this email already exists")
    
    if data.phone and customer_repo.phone_exists(business_id, data.phone):
        raise HTTPException(status_code=400, detail="Customer with this phone already exists")
    
    return customer_repo.create(business_id, data)


@router.put("/{business_id}/customers/{customer_id}", response_model=Customer)
async def update_customer(business_id: str, customer_id: str, data: CustomerUpdate):
    """Update a customer."""
    customer = customer_repo.update(business_id, customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{business_id}/customers/{customer_id}")
async def delete_customer(business_id: str, customer_id: str):
    """Delete a customer."""
    if not customer_repo.delete_by_id_and_business(customer_id, business_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}


@router.post("/{business_id}/customers/import")
async def import_customers_csv(business_id: str, file: UploadFile = File(...)):
    """Import customers from CSV file. Expected columns: first_name, last_name, email, mobile_number"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    skipped = 0
    errors = []
    
    for i, row in enumerate(reader, start=2):
        try:
            first_name = row.get('first_name', '').strip()
            if not first_name:
                skipped += 1
                continue
            
            last_name = row.get('last_name', '').strip() or None
            email = row.get('email', '').strip() or None
            phone = row.get('mobile_number', '').strip() or None
            
            if not email and not phone:
                skipped += 1
                continue
            
            customer_repo.upsert_from_csv(business_id, first_name, last_name, email, phone)
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10]
    }
