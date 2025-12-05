"""Customer identification and history tools for V2."""
from datetime import datetime
from typing import Optional

from app.repositories import customer_repo, appointment_repo, service_repo


def identify_customer(
    business_id: str,
    phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """Identify if a customer is new or returning."""
    if not phone and not email:
        return {
            'customer_id': None,
            'name': None,
            'is_returning': False,
            'visit_count': 0,
            'last_visit': None,
            'message': 'No contact information provided to identify customer.'
        }
    
    customer = customer_repo.find_by_phone_or_email(business_id, phone, email)
    
    if not customer:
        return {
            'customer_id': None,
            'name': None,
            'is_returning': False,
            'visit_count': 0,
            'last_visit': None,
            'message': 'Welcome! This appears to be your first visit with us.'
        }
    
    last_visit = None
    if customer.last_visit_date:
        last_appt = appointment_repo.get_last_completed(customer.id)
        if last_appt:
            last_visit = {
                'date': last_appt['date'],
                'service': last_appt['service_name']
            }
    
    favorite_service = None
    if customer.favorite_service_id:
        favorite_service = service_repo.get_name(customer.favorite_service_id)
    
    name = customer.first_name
    if customer.last_name:
        name += f" {customer.last_name}"
    
    return {
        'customer_id': customer.id,
        'name': name,
        'first_name': customer.first_name,
        'is_returning': True,
        'visit_count': customer.visit_count,
        'last_visit': last_visit,
        'favorite_service': favorite_service,
        'message': f"Welcome back, {customer.first_name}!" + (
            f" Your last visit was on {last_visit['date']} for a {last_visit['service']}."
            if last_visit else ""
        )
    }


def get_customer_history(
    business_id: str,
    customer_id: str
) -> dict:
    """Get visit history for a returning customer."""
    customer = customer_repo.find_with_service_name(business_id, customer_id)
    
    if not customer:
        return {'error': 'Customer not found'}
    
    name = customer.first_name
    if customer.last_name:
        name += f" {customer.last_name}"
    
    appointments = appointment_repo.get_customer_history(customer_id, limit=20)
    
    visits = []
    dates = []
    service_counts = {}
    
    for appt in appointments:
        visits.append({
            'date': appt['date'],
            'service': appt['service_name'],
            'service_id': appt['service_id'],
            'staff_name': appt['staff_name'],
            'notes': appt['notes']
        })
        dates.append(datetime.strptime(appt['date'], '%Y-%m-%d'))
        service_counts[appt['service_name']] = service_counts.get(appt['service_name'], 0) + 1
    
    avg_frequency = None
    if len(dates) >= 2:
        total_days = (dates[0] - dates[-1]).days
        avg_frequency = total_days // (len(dates) - 1) if len(dates) > 1 else None
    
    favorite_service = None
    if service_counts:
        favorite_service = max(service_counts, key=service_counts.get)
    
    return {
        'customer_id': customer_id,
        'name': name,
        'visits': visits,
        'total_visits': customer.visit_count,
        'favorite_service': favorite_service,
        'average_visit_frequency_days': avg_frequency
    }


def create_or_update_customer(
    business_id: str,
    first_name: str,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """Create a new customer or update existing one."""
    existing = None
    if phone:
        existing = customer_repo.find_by_phone(business_id, phone)
    
    if not existing and email:
        existing = customer_repo.find_by_email(business_id, email)
    
    if existing:
        from app.models.customer import CustomerUpdate
        customer_repo.update(
            business_id, 
            existing.id, 
            CustomerUpdate(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                notes=notes
            )
        )
        return {'customer_id': existing.id, 'created': False}
    
    customer_id = customer_repo.create_simple(
        business_id=business_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        notes=notes
    )
    
    return {'customer_id': customer_id, 'created': True}


def get_rebooking_suggestion(
    business_id: str,
    customer_id: str
) -> dict:
    """Get a rebooking suggestion for a returning customer."""
    history = get_customer_history(business_id, customer_id)
    
    if 'error' in history:
        return history
    
    if not history['visits']:
        return {'suggestion': None, 'message': 'No visit history to base suggestion on.'}
    
    last_visit = history['visits'][0]
    favorite = history['favorite_service']
    avg_freq = history['average_visit_frequency_days']
    
    last_date = datetime.strptime(last_visit['date'], '%Y-%m-%d')
    days_since = (datetime.now() - last_date).days
    
    suggestion = {
        'service': favorite or last_visit['service'],
        'service_id': last_visit['service_id'],
        'days_since_last_visit': days_since,
        'average_frequency': avg_freq
    }
    
    if avg_freq and days_since >= avg_freq:
        suggestion['message'] = (
            f"It's been {days_since} days since your last {last_visit['service']}. "
            f"Based on your usual {avg_freq}-day schedule, you're due for another visit! "
            f"Would you like to book your {favorite or last_visit['service']}?"
        )
    elif days_since > 30:
        suggestion['message'] = (
            f"It's been {days_since} days since your last visit. "
            f"Would you like to schedule your next {favorite or last_visit['service']}?"
        )
    else:
        suggestion['message'] = (
            f"Your last visit was {days_since} days ago for a {last_visit['service']}. "
            f"Let me know if you'd like to book another appointment!"
        )
    
    return suggestion
