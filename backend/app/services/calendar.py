"""Mock calendar service for appointment availability."""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_db_connection


def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """Parse date range string into start and end dates."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    date_range_lower = date_range.lower().strip()
    
    if date_range_lower in ['today']:
        return today, today
    elif date_range_lower in ['tomorrow']:
        tomorrow = today + timedelta(days=1)
        return tomorrow, tomorrow
    elif date_range_lower in ['this week', 'week']:
        end = today + timedelta(days=7)
        return today, end
    elif date_range_lower in ['next week']:
        start = today + timedelta(days=7)
        end = today + timedelta(days=14)
        return start, end
    elif date_range_lower in ['this month', 'month']:
        end = today + timedelta(days=30)
        return today, end
    else:
        # Try to parse as date or date range
        try:
            if '-' in date_range and len(date_range.split('-')) > 2:
                # Date range like "Dec 15-20" or "2024-12-15 to 2024-12-20"
                if ' to ' in date_range:
                    parts = date_range.split(' to ')
                    start = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
                    end = datetime.strptime(parts[1].strip(), '%Y-%m-%d')
                    return start, end
                else:
                    # Single date
                    date = datetime.strptime(date_range, '%Y-%m-%d')
                    return date, date
            else:
                # Try single date format
                date = datetime.strptime(date_range, '%Y-%m-%d')
                return date, date
        except ValueError:
            # Default to this week
            return today, today + timedelta(days=7)


def parse_time_preference(time_pref: Optional[str]) -> tuple[int, int]:
    """Parse time preference into start and end hours."""
    if not time_pref:
        return 9, 18  # Default business hours
    
    time_pref_lower = time_pref.lower().strip()
    
    if time_pref_lower in ['morning', 'am']:
        return 9, 12
    elif time_pref_lower in ['afternoon']:
        return 12, 17
    elif time_pref_lower in ['evening', 'late', 'after 5pm', 'after 5']:
        return 17, 20
    elif 'after' in time_pref_lower:
        # Parse "after X" or "after Xpm"
        import re
        match = re.search(r'after\s*(\d+)', time_pref_lower)
        if match:
            hour = int(match.group(1))
            if 'pm' in time_pref_lower and hour < 12:
                hour += 12
            return hour, 20
    elif 'before' in time_pref_lower:
        import re
        match = re.search(r'before\s*(\d+)', time_pref_lower)
        if match:
            hour = int(match.group(1))
            if 'pm' in time_pref_lower and hour < 12:
                hour += 12
            return 9, hour
    
    return 9, 18


def get_business_hours_for_day(config: dict, day_name: str) -> tuple[str, str] | None:
    """Get business hours for a specific day from config."""
    hours = config.get('hours', {})
    day_lower = day_name.lower()
    
    if day_lower in hours:
        day_hours = hours[day_lower]
        if day_hours.get('closed', False):
            return None
        return day_hours.get('open', '09:00'), day_hours.get('close', '18:00')
    
    # Default hours if not specified
    return '09:00', '18:00'


def generate_time_slots(
    date: datetime,
    duration_minutes: int,
    business_hours: tuple[str, str],
    time_start: int,
    time_end: int,
    booked_slots: list[tuple[str, str, int]],
    staff_id: Optional[str] = None,
    staff_name: Optional[str] = None
) -> list[dict]:
    """Generate available time slots for a date."""
    slots = []
    
    # Parse business hours
    open_time = datetime.strptime(business_hours[0], '%H:%M')
    close_time = datetime.strptime(business_hours[1], '%H:%M')
    
    # Adjust for time preference
    start_hour = max(open_time.hour, time_start)
    end_hour = min(close_time.hour, time_end)
    
    current_time = datetime.combine(date.date(), datetime.min.time().replace(hour=start_hour))
    end_time = datetime.combine(date.date(), datetime.min.time().replace(hour=end_hour))
    
    # Get current datetime to filter out past slots
    now = datetime.now()
    
    while current_time + timedelta(minutes=duration_minutes) <= end_time:
        time_str = current_time.strftime('%H:%M')
        
        # Skip past time slots (for today)
        if date.date() == now.date() and current_time <= now:
            current_time += timedelta(minutes=30)
            continue
        
        # Check if this slot conflicts with any booked appointment
        is_available = True
        slot_start = current_time
        slot_end = current_time + timedelta(minutes=duration_minutes)
        
        for booked_time, booked_staff, booked_duration in booked_slots:
            if staff_id and booked_staff and staff_id != booked_staff:
                continue  # Different staff, no conflict
            
            booked_start = datetime.combine(date.date(), datetime.strptime(booked_time, '%H:%M').time())
            booked_end = booked_start + timedelta(minutes=booked_duration)
            
            # Check for overlap
            if not (slot_end <= booked_start or slot_start >= booked_end):
                is_available = False
                break
        
        if is_available:
            slots.append({
                'id': f"{date.strftime('%Y-%m-%d')}_{time_str}_{staff_id or 'any'}",
                'date': date.strftime('%Y-%m-%d'),
                'time': time_str,
                'staff_id': staff_id,
                'staff_name': staff_name,
                'duration_minutes': duration_minutes
            })
        
        # Move to next 30-minute slot
        current_time += timedelta(minutes=30)
    
    return slots


def check_availability(
    business_id: str,
    service_id: str,
    date_range: str,
    time_preference: Optional[str] = None,
    staff_id: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Check available appointment slots.
    
    Args:
        business_id: Business ID
        service_id: Service ID to book
        date_range: Date range string (e.g., "this week", "tomorrow")
        time_preference: Time preference (e.g., "morning", "after 5pm")
        staff_id: Optional specific staff member
        config: Business config (optional, will fetch if not provided)
    
    Returns:
        Available slots and calendar UI data
    """
    # Get service details from config (services are stored in YAML, not DB)
    service_name = None
    duration = 60  # Default duration
    
    if config and config.get('services'):
        for s in config['services']:
            if s.get('id') == service_id or s.get('name', '').lower().replace(' ', '_') == service_id:
                service_name = s.get('name', service_id)
                duration = s.get('duration_minutes', 60)
                break
    
    if not service_name:
        # Use the service_id as name if nothing found in config
        service_name = service_id.replace('_', ' ').title()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get staff members who offer this service
        cursor.execute(
            "SELECT id, name, services_offered FROM staff WHERE business_id = ? AND is_active = 1",
            (business_id,)
        )
        staff_rows = cursor.fetchall()
        
        available_staff = []
        for row in staff_rows:
            services = json.loads(row['services_offered'] or '[]')
            if not services or service_id in services:
                available_staff.append({'id': row['id'], 'name': row['name']})
        
        # If specific staff requested, filter
        if staff_id:
            available_staff = [s for s in available_staff if s['id'] == staff_id]
        
        # If no staff found, use "any"
        if not available_staff:
            available_staff = [{'id': None, 'name': None}]
        
        # Parse date range and time preference
        start_date, end_date = parse_date_range(date_range)
        time_start, time_end = parse_time_preference(time_preference)
        
        # Get existing appointments in this range
        cursor.execute("""
            SELECT date, time, duration_minutes, staff_id FROM appointments 
            WHERE business_id = ? 
            AND date >= ? AND date <= ?
            AND status NOT IN ('cancelled', 'no_show')
        """, (business_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        existing_appts = cursor.fetchall()
        booked_by_date = {}
        for appt in existing_appts:
            date = appt['date']
            if date not in booked_by_date:
                booked_by_date[date] = []
            booked_by_date[date].append((appt['time'], appt['staff_id'], appt['duration_minutes']))
        
        # Generate slots for each day and staff member
        all_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_name = current_date.strftime('%A').lower()
            business_hours = get_business_hours_for_day(config or {}, day_name)
            
            if business_hours:  # Business is open
                date_str = current_date.strftime('%Y-%m-%d')
                booked = booked_by_date.get(date_str, [])
                
                for staff in available_staff:
                    slots = generate_time_slots(
                        current_date,
                        duration,
                        business_hours,
                        time_start,
                        time_end,
                        booked,
                        staff['id'],
                        staff['name']
                    )
                    all_slots.extend(slots)
            
            current_date += timedelta(days=1)
        
        # Limit to reasonable number
        all_slots = all_slots[:20]
        
        return {
            'slots': all_slots,
            'service_id': service_id,
            'service_name': service_name,
            'date_range': date_range,
            'calendar_ui_data': {
                'min_date': start_date.strftime('%Y-%m-%d'),
                'max_date': end_date.strftime('%Y-%m-%d'),
                'available_dates': list(set(s['date'] for s in all_slots)),
                'time_slots': list(set(s['time'] for s in all_slots))
            }
        }


def book_appointment(
    business_id: str,
    service_id: str,
    slot_id: str,
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str] = None,
    customer_id: Optional[str] = None,
    notes: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Book an appointment.
    
    Args:
        business_id: Business ID
        service_id: Service ID
        slot_id: Slot ID from check_availability
        customer_name: Customer name
        customer_phone: Customer phone
        customer_email: Customer email (optional)
        customer_id: Customer ID if returning customer
        notes: Appointment notes
        config: Business config (optional, for service lookup)
    
    Returns:
        Booking confirmation
    """
    # Parse slot_id: format is "YYYY-MM-DD_HH:MM_staffid"
    try:
        parts = slot_id.split('_')
        date = parts[0]
        time = parts[1]
        staff_id = parts[2] if len(parts) > 2 and parts[2] != 'any' else None
    except (IndexError, ValueError):
        return {'error': 'Invalid slot ID'}
    
    # Get service details from config first
    service_name = None
    duration = 60
    
    if config and config.get('services'):
        for s in config['services']:
            if s.get('id') == service_id or s.get('name', '').lower().replace(' ', '_') == service_id:
                service_name = s.get('name', service_id)
                duration = s.get('duration_minutes', 60)
                break
    
    if not service_name:
        # Use service_id as name
        service_name = service_id.replace('_', ' ').title()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get staff name if staff_id provided
        staff_name = None
        if staff_id:
            cursor.execute("SELECT name FROM staff WHERE id = ?", (staff_id,))
            staff_row = cursor.fetchone()
            if staff_row:
                staff_name = staff_row['name']
        
        # Check if slot is still available
        cursor.execute("""
            SELECT id FROM appointments 
            WHERE business_id = ? AND date = ? AND time = ?
            AND status NOT IN ('cancelled', 'no_show')
        """, (business_id, date, time))
        
        if cursor.fetchone():
            return {'error': 'This time slot is no longer available'}
        
        # Create appointment
        appointment_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO appointments 
            (id, business_id, customer_id, service_id, staff_id, customer_name, 
             customer_phone, customer_email, date, time, duration_minutes, status, 
             notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
        """, (
            appointment_id, business_id, customer_id, service_id, staff_id,
            customer_name, customer_phone, customer_email, date, time,
            duration, notes, now, now
        ))
        
        # Update customer visit count if customer_id provided
        if customer_id:
            cursor.execute("""
                UPDATE customers 
                SET visit_count = visit_count + 1, 
                    last_visit_date = ?,
                    favorite_service_id = ?,
                    updated_at = ?
                WHERE id = ?
            """, (date, service_id, now, customer_id))
        
        conn.commit()
        
        # Format time for display
        try:
            time_obj = datetime.strptime(time, '%H:%M')
            time_display = time_obj.strftime('%I:%M %p')
        except ValueError:
            time_display = time
        
        # Format date for display
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_display = date_obj.strftime('%B %d, %Y')
        except ValueError:
            date_display = date
        
        return {
            'confirmation_id': appointment_id,
            'service': service_name,
            'date': date_display,
            'time': time_display,
            'duration_minutes': duration,
            'staff_name': staff_name,
            'customer_name': customer_name,
            'message': f"Your {service_name} appointment has been booked for {date_display} at {time_display}."
        }


def cancel_appointment(
    business_id: str,
    customer_phone: str,
    appointment_id: Optional[str] = None
) -> dict:
    """
    Cancel an appointment.
    
    Args:
        business_id: Business ID
        customer_phone: Customer phone to find appointment
        appointment_id: Specific appointment ID (optional)
    
    Returns:
        Cancellation result
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if appointment_id:
            cursor.execute("""
                SELECT id, date, time, service_id FROM appointments 
                WHERE id = ? AND business_id = ? AND status = 'scheduled'
            """, (appointment_id, business_id))
        else:
            # Find upcoming appointment for this customer
            cursor.execute("""
                SELECT id, date, time, service_id FROM appointments 
                WHERE business_id = ? AND customer_phone = ? 
                AND status = 'scheduled' AND date >= ?
                ORDER BY date, time LIMIT 1
            """, (business_id, customer_phone, datetime.now().strftime('%Y-%m-%d')))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            return {'cancelled': False, 'message': "No upcoming appointment found to cancel."}
        
        # Get service name
        cursor.execute("SELECT name FROM services WHERE id = ?", (appointment['service_id'],))
        service = cursor.fetchone()
        service_name = service['name'] if service else 'appointment'
        
        # Cancel the appointment
        cursor.execute("""
            UPDATE appointments SET status = 'cancelled', updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), appointment['id']))
        conn.commit()
        
        return {
            'cancelled': True,
            'appointment_id': appointment['id'],
            'message': f"Your {service_name} on {appointment['date']} at {appointment['time']} has been cancelled."
        }


def reschedule_appointment(
    business_id: str,
    appointment_id: str,
    new_slot_id: str
) -> dict:
    """
    Reschedule an appointment to a new time slot.
    
    Args:
        business_id: Business ID
        appointment_id: Appointment to reschedule
        new_slot_id: New slot ID
    
    Returns:
        Rescheduling confirmation
    """
    # Parse new slot_id
    try:
        parts = new_slot_id.split('_')
        new_date = parts[0]
        new_time = parts[1]
        new_staff_id = parts[2] if len(parts) > 2 and parts[2] != 'any' else None
    except (IndexError, ValueError):
        return {'error': 'Invalid slot ID'}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get existing appointment
        cursor.execute("""
            SELECT id, service_id, customer_name, staff_id FROM appointments 
            WHERE id = ? AND business_id = ? AND status = 'scheduled'
        """, (appointment_id, business_id))
        
        appointment = cursor.fetchone()
        if not appointment:
            return {'error': 'Appointment not found or already cancelled'}
        
        # Check if new slot is available
        cursor.execute("""
            SELECT id FROM appointments 
            WHERE business_id = ? AND date = ? AND time = ? AND id != ?
            AND status NOT IN ('cancelled', 'no_show')
        """, (business_id, new_date, new_time, appointment_id))
        
        if cursor.fetchone():
            return {'error': 'The new time slot is not available'}
        
        # Update appointment
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE appointments 
            SET date = ?, time = ?, staff_id = COALESCE(?, staff_id), updated_at = ?
            WHERE id = ?
        """, (new_date, new_time, new_staff_id, now, appointment_id))
        conn.commit()
        
        # Get service name
        cursor.execute("SELECT name FROM services WHERE id = ?", (appointment['service_id'],))
        service = cursor.fetchone()
        service_name = service['name'] if service else 'appointment'
        
        # Format for display
        try:
            time_display = datetime.strptime(new_time, '%H:%M').strftime('%I:%M %p')
            date_display = datetime.strptime(new_date, '%Y-%m-%d').strftime('%B %d, %Y')
        except ValueError:
            time_display = new_time
            date_display = new_date
        
        return {
            'new_confirmation_id': appointment_id,
            'new_date': date_display,
            'new_time': time_display,
            'service': service_name,
            'message': f"Your {service_name} has been rescheduled to {date_display} at {time_display}."
        }
