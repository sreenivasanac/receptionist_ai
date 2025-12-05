"""Lead capture and waitlist tools for V2."""
import uuid
import json
from datetime import datetime
from typing import Optional

from app.db.database import get_db_connection


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
    """
    Capture lead for sales follow-up.
    
    Args:
        business_id: Business ID
        name: Lead's name
        interest: What they're interested in
        email: Email address (optional)
        phone: Phone number (optional)
        notes: Additional notes (optional)
        company: Company name for B2B (optional)
        source: Lead source (default: chatbot)
    
    Returns:
        {"lead_id", "message"}
    """
    if not email and not phone:
        return {'error': 'At least email or phone is required', 'lead_id': None}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check for existing lead with same contact
        if email:
            cursor.execute(
                "SELECT id FROM leads WHERE business_id = ? AND email = ?",
                (business_id, email)
            )
            existing = cursor.fetchone()
            if existing:
                # Update existing lead
                cursor.execute("""
                    UPDATE leads SET 
                        name = ?, interest = ?, phone = COALESCE(?, phone),
                        notes = COALESCE(?, notes), company = COALESCE(?, company),
                        updated_at = ?
                    WHERE id = ?
                """, (name, interest, phone, notes, company, 
                      datetime.now().isoformat(), existing['id']))
                conn.commit()
                return {
                    'lead_id': existing['id'],
                    'message': f"Thank you, {name}! We've updated your information. Our team will reach out soon."
                }
        
        # Create new lead
        lead_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO leads 
            (id, business_id, name, email, phone, interest, notes, company, source, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
        """, (lead_id, business_id, name, email, phone, interest, notes, company, source, now, now))
        conn.commit()
        
        return {
            'lead_id': lead_id,
            'message': f"Thank you, {name}! Your information has been captured. Our team will follow up within 24 hours to discuss {interest}."
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
    """
    Add customer to waitlist for a service.
    
    Args:
        business_id: Business ID
        service_id: Service they want
        customer_name: Customer's name
        customer_contact: Contact info (phone/email based on method)
        preferred_dates: List of preferred dates
        preferred_times: List of preferred time slots
        contact_method: How to contact them (phone/email/sms)
        customer_id: Customer ID if known
        notes: Additional notes
    
    Returns:
        {"waitlist_id", "position", "message"}
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get service name
        cursor.execute(
            "SELECT name FROM services WHERE id = ? AND business_id = ?",
            (service_id, business_id)
        )
        service = cursor.fetchone()
        service_name = service['name'] if service else 'service'
        
        # Check if already on waitlist for this service
        cursor.execute("""
            SELECT id FROM waitlist 
            WHERE business_id = ? AND service_id = ? AND customer_contact = ?
            AND status = 'waiting'
        """, (business_id, service_id, customer_contact))
        
        existing = cursor.fetchone()
        if existing:
            # Update preferences
            cursor.execute("""
                UPDATE waitlist SET 
                    preferred_dates = ?, preferred_times = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(preferred_dates), json.dumps(preferred_times),
                  datetime.now().isoformat(), existing['id']))
            conn.commit()
            
            # Get position
            cursor.execute("""
                SELECT COUNT(*) as position FROM waitlist 
                WHERE business_id = ? AND service_id = ? AND status = 'waiting'
                AND created_at <= (SELECT created_at FROM waitlist WHERE id = ?)
            """, (business_id, service_id, existing['id']))
            pos = cursor.fetchone()['position']
            
            return {
                'waitlist_id': existing['id'],
                'position': pos,
                'service_name': service_name,
                'message': f"Your waitlist preferences have been updated. You are #{pos} on the waitlist for {service_name}."
            }
        
        # Add to waitlist
        waitlist_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO waitlist 
            (id, business_id, customer_id, service_id, customer_name, customer_contact,
             preferred_dates, preferred_times, contact_method, status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting', ?, ?, ?)
        """, (waitlist_id, business_id, customer_id, service_id, customer_name, 
              customer_contact, json.dumps(preferred_dates), json.dumps(preferred_times),
              contact_method, notes, now, now))
        conn.commit()
        
        # Get position
        cursor.execute("""
            SELECT COUNT(*) as position FROM waitlist 
            WHERE business_id = ? AND service_id = ? AND status = 'waiting'
        """, (business_id, service_id))
        position = cursor.fetchone()['position']
        
        return {
            'waitlist_id': waitlist_id,
            'position': position,
            'service_name': service_name,
            'message': f"You've been added to the waitlist for {service_name}. You are #{position}. We'll contact you as soon as a slot opens up!"
        }


def get_lead(business_id: str, lead_id: str) -> dict:
    """Get a lead by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM leads WHERE id = ? AND business_id = ?",
            (lead_id, business_id)
        )
        lead = cursor.fetchone()
        
        if not lead:
            return {'error': 'Lead not found'}
        
        return dict(lead)


def update_lead_status(business_id: str, lead_id: str, status: str) -> dict:
    """Update a lead's status."""
    valid_statuses = ['new', 'contacted', 'qualified', 'converted', 'lost']
    if status not in valid_statuses:
        return {'error': f'Invalid status. Must be one of: {valid_statuses}'}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leads SET status = ?, updated_at = ?
            WHERE id = ? AND business_id = ?
        """, (status, datetime.now().isoformat(), lead_id, business_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            return {'error': 'Lead not found'}
        
        return {'lead_id': lead_id, 'status': status, 'message': 'Lead status updated'}
