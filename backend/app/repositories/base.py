"""Base repository class with common CRUD operations."""
import uuid
from datetime import datetime
from typing import Optional, TypeVar, Generic
from abc import ABC, abstractmethod

from app.db.database import get_db_connection

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository providing common database operations."""
    
    table_name: str = ""
    
    def __init__(self):
        if not self.table_name:
            raise ValueError("table_name must be defined in subclass")
    
    @abstractmethod
    def _row_to_model(self, row) -> T:
        """Convert a database row to a model instance."""
        pass
    
    def _generate_id(self) -> str:
        """Generate a new UUID."""
        return str(uuid.uuid4())
    
    def _now(self) -> str:
        """Get current timestamp as ISO string."""
        return datetime.now().isoformat()
    
    def find_by_id(self, id: str) -> Optional[T]:
        """Find a record by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_by_id_and_business(self, id: str, business_id: str) -> Optional[T]:
        """Find a record by ID within a specific business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ? AND business_id = ?",
                (id, business_id)
            )
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_all_by_business(
        self,
        business_id: str,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> list[T]:
        """Find all records for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE business_id = ? ORDER BY {order_by} LIMIT ? OFFSET ?",
                (business_id, limit, offset)
            )
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]
    
    def count_by_business(self, business_id: str) -> int:
        """Count records for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) as count FROM {self.table_name} WHERE business_id = ?",
                (business_id,)
            )
            return cursor.fetchone()["count"]
    
    def delete_by_id(self, id: str) -> bool:
        """Delete a record by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_by_id_and_business(self, id: str, business_id: str) -> bool:
        """Delete a record by ID within a specific business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ? AND business_id = ?",
                (id, business_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def exists(self, id: str) -> bool:
        """Check if a record exists by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {self.table_name} WHERE id = ?", (id,))
            return cursor.fetchone() is not None
    
    def exists_in_business(self, id: str, business_id: str) -> bool:
        """Check if a record exists within a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE id = ? AND business_id = ?",
                (id, business_id)
            )
            return cursor.fetchone() is not None
