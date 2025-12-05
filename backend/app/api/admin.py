"""Admin panel API endpoints for staff and service management."""
from fastapi import APIRouter, HTTPException, Query

from app.repositories import staff_repo, service_repo, business_repo
from app.models.service import Service, ServiceCreate
from app.models.staff import Staff, StaffCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============ STAFF ENDPOINTS ============

@router.get("/{business_id}/staff", response_model=list[Staff])
async def list_staff(business_id: str, active_only: bool = Query(default=True)):
    """List all staff members for a business."""
    return staff_repo.find_by_business(business_id, active_only)


@router.post("/{business_id}/staff", response_model=Staff)
async def create_staff(business_id: str, staff_data: StaffCreate):
    """Create a new staff member."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    return staff_repo.create(business_id, staff_data)


@router.get("/{business_id}/staff/{staff_id}", response_model=Staff)
async def get_staff(business_id: str, staff_id: str):
    """Get a specific staff member."""
    staff = staff_repo.find_by_id_and_business(staff_id, business_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


@router.put("/{business_id}/staff/{staff_id}", response_model=Staff)
async def update_staff(business_id: str, staff_id: str, staff_data: StaffCreate):
    """Update a staff member."""
    staff = staff_repo.update(business_id, staff_id, staff_data)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


@router.delete("/{business_id}/staff/{staff_id}")
async def delete_staff(business_id: str, staff_id: str, hard_delete: bool = Query(default=False)):
    """Delete (or deactivate) a staff member."""
    if not staff_repo.exists_in_business(staff_id, business_id):
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    if hard_delete:
        staff_repo.delete_by_id_and_business(staff_id, business_id)
        return {"message": "Staff member deleted"}
    else:
        staff_repo.deactivate(business_id, staff_id)
        return {"message": "Staff member deactivated"}


# ============ SERVICES ENDPOINTS ============

@router.get("/{business_id}/services", response_model=list[Service])
async def list_services(business_id: str, active_only: bool = Query(default=True)):
    """List all services for a business."""
    return service_repo.find_by_business(business_id, active_only)


@router.post("/{business_id}/services", response_model=Service)
async def create_service(business_id: str, service_data: ServiceCreate):
    """Create a new service."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    return service_repo.create(business_id, service_data)


@router.put("/{business_id}/services/{service_id}", response_model=Service)
async def update_service(business_id: str, service_id: str, service_data: ServiceCreate):
    """Update a service."""
    service = service_repo.update(business_id, service_id, service_data)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.delete("/{business_id}/services/{service_id}")
async def delete_service(business_id: str, service_id: str, hard_delete: bool = Query(default=False)):
    """Delete (or deactivate) a service."""
    if not service_repo.exists_in_business(service_id, business_id):
        raise HTTPException(status_code=404, detail="Service not found")
    
    if hard_delete:
        service_repo.delete_by_id_and_business(service_id, business_id)
        return {"message": "Service deleted"}
    else:
        service_repo.deactivate(business_id, service_id)
        return {"message": "Service deactivated"}
