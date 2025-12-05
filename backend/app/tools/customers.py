"""Customer identification and history tools for V2."""
import uuid
import json
from datetime import datetime
from typing import Optional

from app.db.database import get_db_connection


def identify_customer(
    business_id: str,
    phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Identify if a customer is new or returning.
    
    Args:
        business_id: Business ID
        phone: Customer phone number
        email: Customer email address
    
    Returns:
        {
            "customer_id": "...",
            "name": "Sarah Johnson",
            "is_returning": true,
            "visit_count": 5,
            "last_visit": {"date": "2024-11-15", "service": "Deep Tissue Massage"}
        }
    """
    if not phone and not email:
        return {
            'customer_id': None,
            'name': None,
            'is_returning': False,
            'visit_count': 0,
            'last_visit': None,
            'message': 'No contact information provided to identify customer.'
        }
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Try to find customer by phone or email
        query = "SELECT * FROM customers WHERE business_id = ?"
        params = [business_id]
        
        if phone and email:
            query += " AND (phone = ? OR email = ?)"
            params.extend([phone, email])
        elif phone:
            query += " AND phone = ?"
            params.append(phone)
        else:
            query += " AND email = ?"
            params.append(email)
        
        cursor.execute(query, params)
        customer = cursor.fetchone()
        
        if not customer:
            return {
                'customer_id': None,
                'name': None,
                'is_returning': False,
                'visit_count': 0,
                'last_visit': None,
                'message': 'Welcome! This appears to be your first visit with us.'
            }
        
        # Get last visit details
        last_visit = None
        if customer['last_visit_date']:
            cursor.execute("""
                SELECT a.date, a.time, s.name as service_name
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                WHERE a.customer_id = ? AND a.status = 'completed'
                ORDER BY a.date DESC, a.time DESC
                LIMIT 1
            """, (customer['id'],))
            last_appt = cursor.fetchone()
            
            if last_appt:
                last_visit = {
                    'date': last_appt['date'],
                    'service': last_appt['service_name']
                }
        
        # Get favorite service name
        favorite_service = None
        if customer['favorite_service_id']:
            cursor.execute("SELECT name FROM services WHERE id = ?", (customer['favorite_service_id'],))
            fav = cursor.fetchone()
            if fav:
                favorite_service = fav['name']
        
        name = customer['first_name']
        if customer['last_name']:
            name += f" {customer['last_name']}"
        
        return {
            'customer_id': customer['id'],
            'name': name,
            'first_name': customer['first_name'],
            'is_returning': True,
            'visit_count': customer['visit_count'],
            'last_visit': last_visit,
            'favorite_service': favorite_service,
            'message': f"Welcome back, {customer['first_name']}!" + (
                f" Your last visit was on {last_visit['date']} for a {last_visit['service']}."
                if last_visit else ""
            )
        }


def get_customer_history(
    business_id: str,
    customer_id: str
) -> dict:
    """
    Get visit history for a returning customer.
    
    Args:
        business_id: Business ID
        customer_id: Customer ID
    
    Returns:
        {
            "visits": [{"date", "service", "staff", "notes"}],
            "total_visits": 5,
            "favorite_service": "Deep Tissue Massage",
            "average_visit_frequency_days": 42
        }
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get customer
        cursor.execute(
            "SELECT * FROM customers WHERE id = ? AND business_id = ?",
            (customer_id, business_id)
        )
        customer = cursor.fetchone()
        
        if not customer:
            return {'error': 'Customer not found'}
        
        name = customer['first_name']
        if customer['last_name']:
            name += f" {customer['last_name']}"
        
        # Get appointment history
        cursor.execute("""
            SELECT a.date, a.time, a.notes, s.name as service_name, s.id as service_id,
                   st.name as staff_name
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            LEFT JOIN staff st ON a.staff_id = st.id
            WHERE a.customer_id = ? AND a.status = 'completed'
            ORDER BY a.date DESC, a.time DESC
            LIMIT 20
        """, (customer_id,))
        
        appointments = cursor.fetchall()
        
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
        
        # Calculate average frequency
        avg_frequency = None
        if len(dates) >= 2:
            total_days = (dates[0] - dates[-1]).days
            avg_frequency = total_days // (len(dates) - 1) if len(dates) > 1 else None
        
        # Determine favorite service
        favorite_service = None
        if service_counts:
            favorite_service = max(service_counts, key=service_counts.get)
        
        return {
            'customer_id': customer_id,
            'name': name,
            'visits': visits,
            'total_visits': customer['visit_count'],
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
    """
    Create a new customer or update existing one.
    
    Args:
        business_id: Business ID
        first_name: Customer first name
        last_name: Customer last name
        email: Email address
        phone: Phone number
        notes: Additional notes
    
    Returns:
        Customer record with ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check for existing customer
        existing = None
        if phone:
            cursor.execute(
                "SELECT id FROM customers WHERE business_id = ? AND phone = ?",
                (business_id, phone)
            )
            existing = cursor.fetchone()
        
        if not existing and email:
            cursor.execute(
                "SELECT id FROM customers WHERE business_id = ? AND email = ?",
                (business_id, email)
            )
            existing = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if existing:
            # Update existing customer
            cursor.execute("""
                UPDATE customers SET 
                    first_name = ?, 
                    last_name = COALESCE(?, last_name),
                    email = COALESCE(?, email),
                    phone = COALESCE(?, phone),
                    notes = COALESCE(?, notes),
                    updated_at = ?
                WHERE id = ?
            """, (first_name, last_name, email, phone, notes, now, existing['id']))
            conn.commit()
            
            return {'customer_id': existing['id'], 'created': False}
        
        # Create new customer
        customer_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO customers 
            (id, business_id, first_name, last_name, email, phone, notes, 
             visit_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (customer_id, business_id, first_name, last_name, email, phone, 
              notes, now, now))
        conn.commit()
        
        return {'customer_id': customer_id, 'created': True}


def get_rebooking_suggestion(
    business_id: str,
    customer_id: str
) -> dict:
    """
    Get a rebooking suggestion for a returning customer.
    
    Args:
        business_id: Business ID
        customer_id: Customer ID
    
    Returns:
        Rebooking suggestion based on history
    """
    history = get_customer_history(business_id, customer_id)
    
    if 'error' in history:
        return history
    
    if not history['visits']:
        return {'suggestion': None, 'message': 'No visit history to base suggestion on.'}
    
    last_visit = history['visits'][0]
    favorite = history['favorite_service']
    avg_freq = history['average_visit_frequency_days']
    
    # Calculate days since last visit
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
