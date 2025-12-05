"""Staff repository for data access."""
import json
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.staff import Staff, StaffCreate


class StaffRepository(BaseRepository[Staff]):
    """Repository for staff data access."""
    
    table_name = "staff"
    
    def _row_to_model(self, row) -> Staff:
        """Convert a database row to a Staff model."""
        return Staff(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            role_title=row["role_title"],
            services_offered=json.loads(row["services_offered"] or "[]"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        active_only: bool = True
    ) -> list[Staff]:
        """Find all staff for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM staff WHERE business_id = ?"
            params = [business_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_by_service(
        self,
        business_id: str,
        service_id: str,
        active_only: bool = True
    ) -> list[Staff]:
        """Find staff members who offer a specific service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM staff WHERE business_id = ? AND is_active = 1"
            params = [business_id]
            
            if not active_only:
                query = "SELECT * FROM staff WHERE business_id = ?"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                services = json.loads(row["services_offered"] or "[]")
                if not services or service_id in services:
                    result.append(self._row_to_model(row))
            
            return result
    
    def create(self, business_id: str, data: StaffCreate) -> Staff:
        """Create a new staff member."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            staff_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO staff (id, business_id, name, role_title, services_offered, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                staff_id,
                business_id,
                data.name,
                data.role_title,
                json.dumps(data.services_offered),
                now,
                now
            ))
            conn.commit()
            
            return Staff(
                id=staff_id,
                business_id=business_id,
                name=data.name,
                role_title=data.role_title,
                services_offered=data.services_offered,
                is_active=True,
                created_at=now,
                updated_at=now
            )
    
    def update(self, business_id: str, staff_id: str, data: StaffCreate) -> Optional[Staff]:
        """Update a staff member."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            cursor.execute("""
                UPDATE staff 
                SET name = ?, role_title = ?, services_offered = ?, updated_at = ?
                WHERE id = ? AND business_id = ?
            """, (
                data.name,
                data.role_title,
                json.dumps(data.services_offered),
                now,
                staff_id,
                business_id
            ))
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_by_id_and_business(staff_id, business_id)
    
    def deactivate(self, business_id: str, staff_id: str) -> bool:
        """Soft delete a staff member by deactivating."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE staff SET is_active = 0, updated_at = ? WHERE id = ? AND business_id = ?",
                (self._now(), staff_id, business_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_name(self, staff_id: str) -> Optional[str]:
        """Get staff name by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM staff WHERE id = ?", (staff_id,))
            row = cursor.fetchone()
            return row["name"] if row else None
