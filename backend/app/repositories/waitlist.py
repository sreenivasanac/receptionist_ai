"""Waitlist repository for data access."""
import json
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.lead import WaitlistEntry, WaitlistUpdate


class WaitlistRepository(BaseRepository[WaitlistEntry]):
    """Repository for waitlist data access."""
    
    table_name = "waitlist"
    
    def _row_to_model(self, row) -> WaitlistEntry:
        """Convert a database row to a WaitlistEntry model."""
        try:
            service_name = row["service_name"]
        except (IndexError, KeyError):
            service_name = None
        return WaitlistEntry(
            id=row["id"],
            business_id=row["business_id"],
            customer_id=row["customer_id"],
            service_id=row["service_id"],
            customer_name=row["customer_name"],
            customer_contact=row["customer_contact"],
            preferred_dates=json.loads(row["preferred_dates"] or "[]"),
            preferred_times=json.loads(row["preferred_times"] or "[]"),
            contact_method=row["contact_method"],
            status=row["status"],
            notes=row["notes"],
            service_name=service_name,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        status: Optional[str] = "waiting",
        limit: int = 50
    ) -> list[WaitlistEntry]:
        """Find waitlist entries for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT w.*, s.name as service_name
                FROM waitlist w
                LEFT JOIN services s ON w.service_id = s.id
                WHERE w.business_id = ?
            """
            params = [business_id]
            
            if status:
                query += " AND w.status = ?"
                params.append(status)
            
            query += " ORDER BY w.created_at ASC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_by_contact_and_service(
        self,
        business_id: str,
        service_id: str,
        customer_contact: str
    ) -> Optional[WaitlistEntry]:
        """Find existing waitlist entry for a contact and service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.*, s.name as service_name
                FROM waitlist w
                LEFT JOIN services s ON w.service_id = s.id
                WHERE w.business_id = ? AND w.service_id = ? AND w.customer_contact = ?
                AND w.status = 'waiting'
            """, (business_id, service_id, customer_contact))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_with_service_name(
        self,
        business_id: str,
        waitlist_id: str
    ) -> Optional[WaitlistEntry]:
        """Find a waitlist entry with service name."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT w.*, s.name as service_name
                FROM waitlist w
                LEFT JOIN services s ON w.service_id = s.id
                WHERE w.id = ? AND w.business_id = ?
            """, (waitlist_id, business_id))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def get_position(self, business_id: str, service_id: str, waitlist_id: str) -> int:
        """Get position in waitlist for a service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as position FROM waitlist 
                WHERE business_id = ? AND service_id = ? AND status = 'waiting'
                AND created_at <= (SELECT created_at FROM waitlist WHERE id = ?)
            """, (business_id, service_id, waitlist_id))
            return cursor.fetchone()["position"]
    
    def count_waiting(self, business_id: str, service_id: str) -> int:
        """Count waiting entries for a service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as position FROM waitlist 
                WHERE business_id = ? AND service_id = ? AND status = 'waiting'
            """, (business_id, service_id))
            return cursor.fetchone()["position"]
    
    def create(
        self,
        business_id: str,
        service_id: str,
        customer_name: str,
        customer_contact: str,
        preferred_dates: list[str],
        preferred_times: list[str],
        contact_method: str = 'phone',
        customer_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Create a new waitlist entry and return the ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            waitlist_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO waitlist 
                (id, business_id, customer_id, service_id, customer_name, customer_contact,
                 preferred_dates, preferred_times, contact_method, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting', ?, ?, ?)
            """, (
                waitlist_id,
                business_id,
                customer_id,
                service_id,
                customer_name,
                customer_contact,
                json.dumps(preferred_dates),
                json.dumps(preferred_times),
                contact_method,
                notes,
                now,
                now
            ))
            conn.commit()
            
            return waitlist_id
    
    def update(
        self,
        business_id: str,
        waitlist_id: str,
        data: WaitlistUpdate
    ) -> Optional[WaitlistEntry]:
        """Update a waitlist entry."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if data.preferred_dates is not None:
                updates.append("preferred_dates = ?")
                params.append(json.dumps(data.preferred_dates))
            if data.preferred_times is not None:
                updates.append("preferred_times = ?")
                params.append(json.dumps(data.preferred_times))
            if data.contact_method is not None:
                updates.append("contact_method = ?")
                params.append(data.contact_method)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)
            
            if not updates:
                return None
            
            updates.append("updated_at = ?")
            params.append(self._now())
            params.extend([waitlist_id, business_id])
            
            cursor.execute(f"""
                UPDATE waitlist SET {', '.join(updates)}
                WHERE id = ? AND business_id = ?
            """, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_with_service_name(business_id, waitlist_id)
    
    def update_preferences(
        self,
        waitlist_id: str,
        preferred_dates: list[str],
        preferred_times: list[str]
    ) -> bool:
        """Update waitlist preferences."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE waitlist SET 
                    preferred_dates = ?, preferred_times = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(preferred_dates),
                json.dumps(preferred_times),
                self._now(),
                waitlist_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    # V3 Cancellation Recovery Methods
    
    def find_waiting_for_service_and_date(
        self,
        business_id: str,
        service_id: str,
        date: str,
        time_preference: Optional[str] = None
    ) -> list[WaitlistEntry]:
        """
        Find waitlist entries that match a cancelled appointment slot.
        Returns entries ordered by creation date (first come, first served).
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT w.*, s.name as service_name
                FROM waitlist w
                LEFT JOIN services s ON w.service_id = s.id
                WHERE w.business_id = ? 
                AND w.service_id = ?
                AND w.status = 'waiting'
                AND (w.preferred_dates LIKE ? OR w.preferred_dates = '[]')
                ORDER BY w.created_at ASC
            """, (business_id, service_id, f'%"{date}"%'))
            
            rows = cursor.fetchall()
            entries = [self._row_to_model(row) for row in rows]
            
            if time_preference and entries:
                filtered = []
                for entry in entries:
                    prefs = entry.preferred_times
                    if not prefs or time_preference in prefs or self._time_matches_preference(time_preference, prefs):
                        filtered.append(entry)
                return filtered if filtered else entries[:3]
            
            return entries
    
    def _time_matches_preference(self, slot_time: str, preferences: list[str]) -> bool:
        """Check if a time slot matches time preferences like 'morning', 'afternoon'."""
        try:
            hour = int(slot_time.split(":")[0])
            for pref in preferences:
                pref_lower = pref.lower()
                if pref_lower == "morning" and 6 <= hour < 12:
                    return True
                elif pref_lower == "afternoon" and 12 <= hour < 17:
                    return True
                elif pref_lower == "evening" and 17 <= hour < 21:
                    return True
                elif "after 5" in pref_lower and hour >= 17:
                    return True
                elif "before noon" in pref_lower and hour < 12:
                    return True
        except:
            pass
        return False
    
    def mark_notified(
        self,
        waitlist_id: str,
        cancelled_appointment_id: Optional[str] = None
    ) -> bool:
        """Mark a waitlist entry as notified about available slot."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE waitlist SET status = 'notified', updated_at = ?
                WHERE id = ?
            """, (self._now(), waitlist_id))
            
            if cancelled_appointment_id:
                notification_id = self._generate_id()
                cursor.execute("""
                    INSERT INTO waitlist_notifications 
                    (id, waitlist_id, cancelled_appointment_id, notification_sent_at, response)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (notification_id, waitlist_id, cancelled_appointment_id, self._now()))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_booked(self, waitlist_id: str) -> bool:
        """Mark a waitlist entry as booked (converted)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE waitlist SET status = 'booked', updated_at = ?
                WHERE id = ?
            """, (self._now(), waitlist_id))
            
            cursor.execute("""
                UPDATE waitlist_notifications 
                SET response = 'accepted', response_at = ?, booking_created = 1
                WHERE waitlist_id = ? AND response = 'pending'
            """, (self._now(), waitlist_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_declined(self, waitlist_id: str) -> bool:
        """Mark a waitlist notification as declined."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE waitlist SET status = 'waiting', updated_at = ?
                WHERE id = ?
            """, (self._now(), waitlist_id))
            
            cursor.execute("""
                UPDATE waitlist_notifications 
                SET response = 'declined', response_at = ?
                WHERE waitlist_id = ? AND response = 'pending'
            """, (self._now(), waitlist_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_notification_stats(self, business_id: str) -> dict:
        """Get waitlist notification statistics."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_notifications,
                    SUM(CASE WHEN n.response = 'accepted' THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN n.response = 'declined' THEN 1 ELSE 0 END) as declined,
                    SUM(CASE WHEN n.response = 'expired' THEN 1 ELSE 0 END) as expired,
                    SUM(CASE WHEN n.response = 'pending' THEN 1 ELSE 0 END) as pending
                FROM waitlist_notifications n
                JOIN waitlist w ON n.waitlist_id = w.id
                WHERE w.business_id = ?
            """, (business_id,))
            
            row = cursor.fetchone()
            return {
                "total_notifications": row["total_notifications"] or 0,
                "accepted": row["accepted"] or 0,
                "declined": row["declined"] or 0,
                "expired": row["expired"] or 0,
                "pending": row["pending"] or 0,
                "conversion_rate": (
                    (row["accepted"] / row["total_notifications"] * 100) 
                    if row["total_notifications"] else 0
                )
            }
