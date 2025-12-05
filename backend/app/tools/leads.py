"""Lead capture and waitlist tools for V2."""
from typing import Optional

from app.repositories import lead_repo, waitlist_repo, service_repo


def capture_lead(
    business_id: str,
    name: str,
    interest: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None,
    company: Optional[str] = None,
    source: str = 'chatbot'
) -> dict:
    """Capture lead for sales follow-up."""
    if not email and not phone:
        return {'error': 'At least email or phone is required', 'lead_id': None}
    
    lead_id, is_new = lead_repo.create_or_update(
        business_id=business_id,
        name=name,
        interest=interest,
        email=email,
        phone=phone,
        notes=notes,
        company=company,
        source=source
    )
    
    if is_new:
        return {
            'lead_id': lead_id,
            'message': f"Thank you, {name}! Your information has been captured. Our team will follow up within 24 hours to discuss {interest}."
        }
    else:
        return {
            'lead_id': lead_id,
            'message': f"Thank you, {name}! We've updated your information. Our team will reach out soon."
        }


def add_to_waitlist(
    business_id: str,
    service_id: str,
    customer_name: str,
    customer_contact: str,
    preferred_dates: list[str],
    preferred_times: list[str],
    contact_method: str = 'phone',
    customer_id: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """Add customer to waitlist for a service."""
    service_name = service_repo.get_name(service_id) or 'service'
    
    # Check if already on waitlist
    existing = waitlist_repo.find_by_contact_and_service(
        business_id, service_id, customer_contact
    )
    
    if existing:
        waitlist_repo.update_preferences(
            existing.id, preferred_dates, preferred_times
        )
        position = waitlist_repo.get_position(business_id, service_id, existing.id)
        
        return {
            'waitlist_id': existing.id,
            'position': position,
            'service_name': service_name,
            'message': f"Your waitlist preferences have been updated. You are #{position} on the waitlist for {service_name}."
        }
    
    waitlist_id = waitlist_repo.create(
        business_id=business_id,
        service_id=service_id,
        customer_name=customer_name,
        customer_contact=customer_contact,
        preferred_dates=preferred_dates,
        preferred_times=preferred_times,
        contact_method=contact_method,
        customer_id=customer_id,
        notes=notes
    )
    
    position = waitlist_repo.count_waiting(business_id, service_id)
    
    return {
        'waitlist_id': waitlist_id,
        'position': position,
        'service_name': service_name,
        'message': f"You've been added to the waitlist for {service_name}. You are #{position}. We'll contact you as soon as a slot opens up!"
    }


def get_lead(business_id: str, lead_id: str) -> dict:
    """Get a lead by ID."""
    lead = lead_repo.find_by_id_and_business(lead_id, business_id)
    
    if not lead:
        return {'error': 'Lead not found'}
    
    return {
        'id': lead.id,
        'business_id': lead.business_id,
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'interest': lead.interest,
        'notes': lead.notes,
        'company': lead.company,
        'status': lead.status,
        'source': lead.source,
        'created_at': lead.created_at,
        'updated_at': lead.updated_at
    }


def update_lead_status(business_id: str, lead_id: str, status: str) -> dict:
    """Update a lead's status."""
    valid_statuses = ['new', 'contacted', 'qualified', 'converted', 'lost']
    if status not in valid_statuses:
        return {'error': f'Invalid status. Must be one of: {valid_statuses}'}
    
    if not lead_repo.update_status(business_id, lead_id, status):
        return {'error': 'Lead not found'}
    
    return {'lead_id': lead_id, 'status': status, 'message': 'Lead status updated'}
