"""Mock calendar service for appointment availability."""
from datetime import datetime, timedelta
from typing import Optional

from app.repositories import staff_repo, appointment_repo, customer_repo


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
        try:
            if '-' in date_range and len(date_range.split('-')) > 2:
                if ' to ' in date_range:
                    parts = date_range.split(' to ')
                    start = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
                    end = datetime.strptime(parts[1].strip(), '%Y-%m-%d')
                    return start, end
                else:
                    date = datetime.strptime(date_range, '%Y-%m-%d')
                    return date, date
            else:
                date = datetime.strptime(date_range, '%Y-%m-%d')
                return date, date
        except ValueError:
            return today, today + timedelta(days=7)


def parse_time_preference(time_pref: Optional[str]) -> tuple[int, int]:
    """Parse time preference into start and end hours."""
    if not time_pref:
        return 9, 18
    
    time_pref_lower = time_pref.lower().strip()
    
    if time_pref_lower in ['morning', 'am']:
        return 9, 12
    elif time_pref_lower in ['afternoon']:
        return 12, 17
    elif time_pref_lower in ['evening', 'late', 'after 5pm', 'after 5']:
        return 17, 20
    elif 'after' in time_pref_lower:
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
    
    open_time = datetime.strptime(business_hours[0], '%H:%M')
    close_time = datetime.strptime(business_hours[1], '%H:%M')
    
    start_hour = max(open_time.hour, time_start)
    end_hour = min(close_time.hour, time_end)
    
    current_time = datetime.combine(date.date(), datetime.min.time().replace(hour=start_hour))
    end_time = datetime.combine(date.date(), datetime.min.time().replace(hour=end_hour))
    
    now = datetime.now()
    
    # Calculate actual close time from business hours for duration validation
    actual_close = datetime.combine(date.date(), close_time.time())
    
    while current_time + timedelta(minutes=duration_minutes) <= end_time:
        time_str = current_time.strftime('%H:%M')
        
        # Skip if in the past
        if date.date() == now.date() and current_time <= now:
            current_time += timedelta(minutes=30)
            continue
        
        # Ensure service fits before business closing time (not just preference end time)
        slot_end_actual = current_time + timedelta(minutes=duration_minutes)
        if slot_end_actual > actual_close:
            current_time += timedelta(minutes=30)
            continue
        
        is_available = True
        slot_start = current_time
        slot_end = current_time + timedelta(minutes=duration_minutes)
        
        for booked_time, booked_staff, booked_duration in booked_slots:
            if staff_id and booked_staff and staff_id != booked_staff:
                continue
            
            booked_start = datetime.combine(date.date(), datetime.strptime(booked_time, '%H:%M').time())
            booked_end = booked_start + timedelta(minutes=booked_duration)
            
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
    """Check available appointment slots."""
    service_name = None
    duration = 60
    
    if config and config.get('services'):
        for s in config['services']:
            if s.get('id') == service_id or s.get('name', '').lower().replace(' ', '_') == service_id:
                service_name = s.get('name', service_id)
                duration = s.get('duration_minutes', 60)
                break
    
    if not service_name:
        service_name = service_id.replace('_', ' ').title()
    
    # Get staff who can offer this service
    all_staff = staff_repo.find_by_service(business_id, service_id)
    
    available_staff = [{'id': s.id, 'name': s.name} for s in all_staff]
    
    if staff_id:
        available_staff = [s for s in available_staff if s['id'] == staff_id]
    
    if not available_staff:
        available_staff = [{'id': None, 'name': None}]
    
    # Parse date range - always show 2 months
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=60)
    time_start, time_end = parse_time_preference(time_preference)
    
    # Get existing appointments
    existing_appts = appointment_repo.find_in_date_range(
        business_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d'),
        exclude_statuses=['cancelled', 'no_show']
    )
    
    booked_by_date = {}
    for appt in existing_appts:
        date = appt['date']
        if date not in booked_by_date:
            booked_by_date[date] = []
        booked_by_date[date].append((appt['time'], appt['staff_id'], appt['duration_minutes']))
    
    # Generate slots
    all_slots = []
    current_date = start_date
    
    while current_date <= end_date:
        day_name = current_date.strftime('%A').lower()
        business_hours = get_business_hours_for_day(config or {}, day_name)
        
        if business_hours:
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
    """Book an appointment."""
    try:
        parts = slot_id.split('_')
        date = parts[0]
        time = parts[1]
        staff_id = parts[2] if len(parts) > 2 and parts[2] != 'any' else None
    except (IndexError, ValueError):
        return {'error': 'Invalid slot ID'}
    
    service_name = None
    duration = 60
    
    if config and config.get('services'):
        for s in config['services']:
            if s.get('id') == service_id or s.get('name', '').lower().replace(' ', '_') == service_id:
                service_name = s.get('name', service_id)
                duration = s.get('duration_minutes', 60)
                break
    
    if not service_name:
        service_name = service_id.replace('_', ' ').title()
    
    # Get staff name
    staff_name = None
    if staff_id:
        staff_name = staff_repo.get_name(staff_id)
    
    # Check slot availability with overlap detection
    if not appointment_repo.slot_available(business_id, date, time, duration_minutes=duration):
        return {'error': 'This time slot is no longer available'}
    
    # Find or create customer
    if not customer_id and customer_phone:
        existing = customer_repo.find_by_phone(business_id, customer_phone)
        
        if existing:
            customer_id = existing.id
        else:
            name_parts = customer_name.split(' ', 1) if customer_name else ['Unknown']
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            customer_id = customer_repo.create_simple(
                business_id=business_id,
                first_name=first_name,
                last_name=last_name,
                email=customer_email,
                phone=customer_phone
            )
    
    # Create appointment
    appointment_id = appointment_repo.create_from_booking(
        business_id=business_id,
        customer_id=customer_id,
        service_id=service_id,
        staff_id=staff_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        date=date,
        time=time,
        duration_minutes=duration,
        notes=notes
    )
    
    # Update customer visit
    if customer_id:
        customer_repo.update_visit(customer_id, date, service_id)
    
    # Format for display
    try:
        time_obj = datetime.strptime(time, '%H:%M')
        time_display = time_obj.strftime('%I:%M %p')
    except ValueError:
        time_display = time
    
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
    """Cancel an appointment."""
    if appointment_id:
        appointment = appointment_repo.find_by_id_and_business(appointment_id, business_id)
        if not appointment or appointment.status != 'scheduled':
            return {'cancelled': False, 'message': "No upcoming appointment found to cancel."}
        appt_data = {
            'id': appointment.id,
            'date': appointment.date,
            'time': appointment.time,
            'service_id': appointment.service_id
        }
    else:
        appt_data = appointment_repo.find_upcoming_by_phone(
            business_id, customer_phone, datetime.now().strftime('%Y-%m-%d')
        )
        
        if not appt_data:
            return {'cancelled': False, 'message': "No upcoming appointment found to cancel."}
    
    service_name = appt_data.get('service_id', 'appointment').replace('_', ' ').title()
    
    appointment_repo.update_status(business_id, appt_data['id'], 'cancelled')
    
    return {
        'cancelled': True,
        'appointment_id': appt_data['id'],
        'message': f"Your {service_name} on {appt_data['date']} at {appt_data['time']} has been cancelled."
    }


def reschedule_appointment(
    business_id: str,
    appointment_id: str,
    new_slot_id: str
) -> dict:
    """Reschedule an appointment to a new time slot."""
    try:
        parts = new_slot_id.split('_')
        new_date = parts[0]
        new_time = parts[1]
        new_staff_id = parts[2] if len(parts) > 2 and parts[2] != 'any' else None
    except (IndexError, ValueError):
        return {'error': 'Invalid slot ID'}
    
    appointment = appointment_repo.find_by_id_and_business(appointment_id, business_id)
    if not appointment or appointment.status != 'scheduled':
        return {'error': 'Appointment not found or already cancelled'}
    
    if not appointment_repo.slot_available(business_id, new_date, new_time, appointment_id):
        return {'error': 'The new time slot is not available'}
    
    appointment_repo.reschedule(appointment_id, new_date, new_time, new_staff_id)
    
    service_name = appointment.service_id.replace('_', ' ').title()
    
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
