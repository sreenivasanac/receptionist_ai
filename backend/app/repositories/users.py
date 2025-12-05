"""Users repository for data access."""
import json
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for user data access."""
    
    table_name = "users"
    
    def _row_to_model(self, row) -> User:
        """Convert a database row to a User model."""
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            business_id=row["business_id"],
            created_at=row["created_at"],
            last_login=row["last_login"]
        )
    
    def find_by_id(self, id: str) -> Optional[User]:
        """Find a user by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_by_username_and_role(
        self,
        username: str,
        role: str
    ) -> Optional[dict]:
        """Find a user by username and role, returning raw dict with business info."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, business_id 
                FROM users 
                WHERE username = ? AND role = ?
            """, (username, role))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    
    def create(
        self,
        user_id: str,
        username: str,
        email: Optional[str],
        role: str,
        business_id: Optional[str] = None
    ) -> str:
        """Create a new user and return the ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, email, role, business_id, last_login)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                username,
                email,
                role,
                business_id,
                self._now()
            ))
            conn.commit()
            return user_id
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (self._now(), user_id))
            conn.commit()
    
    def get_business_info(self, business_id: str) -> Optional[dict]:
        """Get business info for login response."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, type, address, phone, email, website, features_enabled
                FROM businesses WHERE id = ?
            """, (business_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "address": row["address"],
                "phone": row["phone"],
                "email": row["email"],
                "website": row["website"],
                "features_enabled": json.loads(row["features_enabled"] or "{}")
            }
