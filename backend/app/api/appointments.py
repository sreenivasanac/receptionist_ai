"""Appointments API endpoints for V2."""
import yaml
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories import appointment_repo, business_repo
from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate

router = APIRouter(prefix="/admin", tags=["Appointments"])


def get_service_name_from_config(config_yaml: str, service_id: str) -> str:
    """Get service name from business config YAML."""
    if not config_yaml or not service_id:
        return None
    try:
        config = yaml.safe_load(config_yaml)
        for service in config.get('services', []):
            if service.get('id') == service_id:
                return service.get('name')
        return service_id.replace('_', ' ').title()
    except:
        return service_id.replace('_', ' ').title() if service_id else None


@router.get("/{business_id}/appointments", response_model=list[Appointment])
async def list_appointments(
    business_id: str,
    status: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100)
):
    """List appointments for a business with optional filters."""
    config_yaml = business_repo.get_config_yaml(business_id)
    appointments = appointment_repo.find_by_business(
        business_id, status, date_from, date_to, limit
    )
    
    for appt in appointments:
        appt.service_name = get_service_name_from_config(config_yaml, appt.service_id)
    
    return appointments


@router.get("/{business_id}/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(business_id: str, appointment_id: str):
    """Get a specific appointment."""
    config_yaml = business_repo.get_config_yaml(business_id)
    appointment = appointment_repo.find_with_staff_name(business_id, appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.service_name = get_service_name_from_config(config_yaml, appointment.service_id)
    return appointment


@router.post("/{business_id}/appointments", response_model=Appointment)
async def create_appointment(business_id: str, data: AppointmentCreate):
    """Create a new appointment (admin booking)."""
    appointment = appointment_repo.create(business_id, data)
    
    config_yaml = business_repo.get_config_yaml(business_id)
    appointment.service_name = get_service_name_from_config(config_yaml, appointment.service_id)
    
    return appointment


@router.put("/{business_id}/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(business_id: str, appointment_id: str, data: AppointmentUpdate):
    """Update an appointment."""
    appointment = appointment_repo.update(business_id, appointment_id, data)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    config_yaml = business_repo.get_config_yaml(business_id)
    appointment.service_name = get_service_name_from_config(config_yaml, appointment.service_id)
    
    return appointment


@router.delete("/{business_id}/appointments/{appointment_id}")
async def delete_appointment(business_id: str, appointment_id: str):
    """Delete an appointment."""
    if not appointment_repo.delete_by_id_and_business(appointment_id, business_id):
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Appointment deleted"}


@router.post("/{business_id}/appointments/{appointment_id}/status")
async def update_appointment_status(business_id: str, appointment_id: str, status: str):
    """Update appointment status (shortcut endpoint)."""
    from app.repositories import customer_repo
    
    valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # Get appointment before updating to access customer info
    appointment = appointment_repo.find_with_staff_name(business_id, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update status
    if not appointment_repo.update_status(business_id, appointment_id, status):
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Update customer visit tracking when marked as completed
    if status == 'completed' and appointment.customer_id:
        customer_repo.update_visit(
            customer_id=appointment.customer_id,
            visit_date=appointment.date,
            service_id=appointment.service_id
        )
    
    return {"appointment_id": appointment_id, "status": status}
