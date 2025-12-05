"""Appointments repository for data access."""
from datetime import datetime
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate


class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for appointment data access."""
    
    table_name = "appointments"
    
    def _row_to_model(
        self,
        row,
        service_name: Optional[str] = None,
        staff_name: Optional[str] = None
    ) -> Appointment:
        """Convert a database row to an Appointment model."""
        resolved_staff_name = staff_name
        if resolved_staff_name is None:
            try:
                resolved_staff_name = row["staff_name"]
            except (IndexError, KeyError):
                resolved_staff_name = None
        return Appointment(
            id=row["id"],
            business_id=row["business_id"],
            customer_id=row["customer_id"],
            service_id=row["service_id"],
            staff_id=row["staff_id"],
            customer_name=row["customer_name"],
            customer_phone=row["customer_phone"],
            customer_email=row["customer_email"],
            date=row["date"],
            time=row["time"],
            duration_minutes=row["duration_minutes"],
            status=row["status"],
            notes=row["notes"],
            service_name=service_name,
            staff_name=resolved_staff_name,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50
    ) -> list[Appointment]:
        """Find appointments for a business with optional filters."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT a.*, st.name as staff_name
                FROM appointments a
                LEFT JOIN staff st ON a.staff_id = st.id
                WHERE a.business_id = ?
            """
            params = [business_id]
            
            if status:
                query += " AND a.status = ?"
                params.append(status)
            
            if date_from:
                query += " AND a.date >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND a.date <= ?"
                params.append(date_to)
            
            query += " ORDER BY a.date DESC, a.time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_with_staff_name(
        self,
        business_id: str,
        appointment_id: str
    ) -> Optional[Appointment]:
        """Find an appointment with staff name."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, st.name as staff_name
                FROM appointments a
                LEFT JOIN staff st ON a.staff_id = st.id
                WHERE a.id = ? AND a.business_id = ?
            """, (appointment_id, business_id))
            
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_in_date_range(
        self,
        business_id: str,
        start_date: str,
        end_date: str,
        exclude_statuses: list[str] = None
    ) -> list[dict]:
        """Find appointments in a date range, returning raw data."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT date, time, duration_minutes, staff_id FROM appointments 
                WHERE business_id = ? 
                AND date >= ? AND date <= ?
            """
            params = [business_id, start_date, end_date]
            
            if exclude_statuses:
                placeholders = ",".join(["?" for _ in exclude_statuses])
                query += f" AND status NOT IN ({placeholders})"
                params.extend(exclude_statuses)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def find_upcoming_by_phone(
        self,
        business_id: str,
        customer_phone: str,
        from_date: str
    ) -> Optional[dict]:
        """Find upcoming appointment for a customer by phone."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, time, service_id FROM appointments 
                WHERE business_id = ? AND customer_phone = ? 
                AND status = 'scheduled' AND date >= ?
                ORDER BY date, time LIMIT 1
            """, (business_id, customer_phone, from_date))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create(
        self,
        business_id: str,
        data: AppointmentCreate
    ) -> Appointment:
        """Create a new appointment."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            appointment_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO appointments 
                (id, business_id, customer_id, service_id, staff_id, customer_name,
                 customer_phone, customer_email, date, time, duration_minutes,
                 status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
            """, (
                appointment_id,
                business_id,
                data.customer_id,
                data.service_id,
                data.staff_id,
                data.customer_name,
                data.customer_phone,
                data.customer_email,
                data.date,
                data.time,
                data.duration_minutes,
                data.notes,
                now,
                now
            ))
            conn.commit()
            
            return self.find_with_staff_name(business_id, appointment_id)
    
    def create_from_booking(
        self,
        business_id: str,
        customer_id: Optional[str],
        service_id: str,
        staff_id: Optional[str],
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str],
        date: str,
        time: str,
        duration_minutes: int,
        notes: Optional[str] = None
    ) -> str:
        """Create an appointment from a booking and return the ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            appointment_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO appointments 
                (id, business_id, customer_id, service_id, staff_id, customer_name, 
                 customer_phone, customer_email, date, time, duration_minutes, status, 
                 notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
            """, (
                appointment_id,
                business_id,
                customer_id,
                service_id,
                staff_id,
                customer_name,
                customer_phone,
                customer_email,
                date,
                time,
                duration_minutes,
                notes,
                now,
                now
            ))
            conn.commit()
            
            return appointment_id
    
    def update(
        self,
        business_id: str,
        appointment_id: str,
        data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """Update an appointment."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if data.service_id is not None:
                updates.append("service_id = ?")
                params.append(data.service_id)
            if data.date is not None:
                updates.append("date = ?")
                params.append(data.date)
            if data.time is not None:
                updates.append("time = ?")
                params.append(data.time)
            if data.duration_minutes is not None:
                updates.append("duration_minutes = ?")
                params.append(data.duration_minutes)
            if data.staff_id is not None:
                updates.append("staff_id = ?")
                params.append(data.staff_id)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)
            
            if not updates:
                return self.find_with_staff_name(business_id, appointment_id)
            
            updates.append("updated_at = ?")
            params.append(self._now())
            params.extend([appointment_id, business_id])
            
            cursor.execute(f"""
                UPDATE appointments SET {', '.join(updates)}
                WHERE id = ? AND business_id = ?
            """, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_with_staff_name(business_id, appointment_id)
    
    def update_status(
        self,
        business_id: str,
        appointment_id: str,
        status: str
    ) -> bool:
        """Update appointment status."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE appointments SET status = ?, updated_at = ?
                WHERE id = ? AND business_id = ?
            """, (status, self._now(), appointment_id, business_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def reschedule(
        self,
        appointment_id: str,
        new_date: str,
        new_time: str,
        new_staff_id: Optional[str] = None
    ) -> bool:
        """Reschedule an appointment."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            cursor.execute("""
                UPDATE appointments 
                SET date = ?, time = ?, staff_id = COALESCE(?, staff_id), updated_at = ?
                WHERE id = ?
            """, (new_date, new_time, new_staff_id, now, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def slot_available(
        self,
        business_id: str,
        date: str,
        time: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """Check if a time slot is available."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id FROM appointments 
                WHERE business_id = ? AND date = ? AND time = ?
                AND status NOT IN ('cancelled', 'no_show')
            """
            params = [business_id, date, time]
            
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            
            cursor.execute(query, params)
            return cursor.fetchone() is None
    
    def get_customer_history(
        self,
        customer_id: str,
        limit: int = 20
    ) -> list[dict]:
        """Get appointment history for a customer."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.date, a.time, a.notes, s.name as service_name, s.id as service_id,
                       st.name as staff_name
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                LEFT JOIN staff st ON a.staff_id = st.id
                WHERE a.customer_id = ? AND a.status = 'completed'
                ORDER BY a.date DESC, a.time DESC
                LIMIT ?
            """, (customer_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_last_completed(self, customer_id: str) -> Optional[dict]:
        """Get last completed appointment for a customer."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.date, a.time, s.name as service_name
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                WHERE a.customer_id = ? AND a.status = 'completed'
                ORDER BY a.date DESC, a.time DESC
                LIMIT 1
            """, (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
