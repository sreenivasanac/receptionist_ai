"""Services repository for data access."""
from datetime import datetime
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.service import Service, ServiceCreate


class ServiceRepository(BaseRepository[Service]):
    """Repository for service data access."""
    
    table_name = "services"
    
    def _row_to_model(self, row) -> Service:
        """Convert a database row to a Service model."""
        return Service(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            description=row["description"],
            duration_minutes=row["duration_minutes"],
            price=row["price"],
            requires_consultation=bool(row["requires_consultation"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        active_only: bool = True
    ) -> list[Service]:
        """Find all services for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM services WHERE business_id = ?"
            params = [business_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def create(self, business_id: str, data: ServiceCreate) -> Service:
        """Create a new service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            service_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO services (id, business_id, name, description, duration_minutes, price, requires_consultation, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                service_id,
                business_id,
                data.name,
                data.description,
                data.duration_minutes,
                data.price,
                1 if data.requires_consultation else 0,
                now,
                now
            ))
            conn.commit()
            
            return Service(
                id=service_id,
                business_id=business_id,
                name=data.name,
                description=data.description,
                duration_minutes=data.duration_minutes,
                price=data.price,
                requires_consultation=data.requires_consultation,
                is_active=True,
                created_at=now,
                updated_at=now
            )
    
    def update(self, business_id: str, service_id: str, data: ServiceCreate) -> Optional[Service]:
        """Update a service."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            cursor.execute("""
                UPDATE services 
                SET name = ?, description = ?, duration_minutes = ?, price = ?, requires_consultation = ?, updated_at = ?
                WHERE id = ? AND business_id = ?
            """, (
                data.name,
                data.description,
                data.duration_minutes,
                data.price,
                1 if data.requires_consultation else 0,
                now,
                service_id,
                business_id
            ))
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_by_id_and_business(service_id, business_id)
    
    def deactivate(self, business_id: str, service_id: str) -> bool:
        """Soft delete a service by deactivating."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE services SET is_active = 0, updated_at = ? WHERE id = ? AND business_id = ?",
                (self._now(), service_id, business_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_name(self, service_id: str) -> Optional[str]:
        """Get service name by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM services WHERE id = ?", (service_id,))
            row = cursor.fetchone()
            return row["name"] if row else None
    
    def sync_from_config(self, business_id: str, services: list[dict]):
        """Sync services from YAML config to database."""
        if not services:
            return
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            cursor.execute("SELECT id FROM services WHERE business_id = ?", (business_id,))
            existing_ids = {row['id'] for row in cursor.fetchall()}
            
            new_ids = set()
            for service in services:
                service_id = service.get('id')
                if not service_id:
                    continue
                
                new_ids.add(service_id)
                
                if service_id in existing_ids:
                    cursor.execute("""
                        UPDATE services 
                        SET name = ?, description = ?, price = ?, duration_minutes = ?, 
                            is_active = ?, updated_at = ?
                        WHERE id = ? AND business_id = ?
                    """, (
                        service.get('name', ''),
                        service.get('description', ''),
                        service.get('price', 0),
                        service.get('duration_minutes', 60),
                        1,
                        now,
                        service_id,
                        business_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO services (id, business_id, name, description, price, 
                                             duration_minutes, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        service_id,
                        business_id,
                        service.get('name', ''),
                        service.get('description', ''),
                        service.get('price', 0),
                        service.get('duration_minutes', 60),
                        1,
                        now,
                        now
                    ))
            
            removed_ids = existing_ids - new_ids
            if removed_ids:
                placeholders = ','.join(['?' for _ in removed_ids])
                cursor.execute(f"""
                    UPDATE services SET is_active = 0, updated_at = ?
                    WHERE business_id = ? AND id IN ({placeholders})
                """, [now, business_id] + list(removed_ids))
            
            conn.commit()
