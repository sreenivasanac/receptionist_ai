"""Conversations repository for data access."""
import json
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for conversation data access."""
    
    table_name = "conversations"
    
    def _row_to_model(self, row) -> dict:
        """Convert a database row to a dict."""
        return {
            "id": row["id"],
            "business_id": row["business_id"],
            "session_id": row["session_id"],
            "messages": json.loads(row["messages"] or "[]"),
            "customer_info": json.loads(row["customer_info"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    def find_by_session(
        self,
        business_id: str,
        session_id: str
    ) -> Optional[dict]:
        """Find a conversation by session ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE business_id = ? AND session_id = ?",
                (business_id, session_id)
            )
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def get_or_create(self, business_id: str, session_id: str) -> dict:
        """Get or create a conversation session."""
        existing = self.find_by_session(business_id, session_id)
        if existing:
            return existing
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            conv_id = self._generate_id()
            
            cursor.execute("""
                INSERT INTO conversations (id, business_id, session_id, messages, customer_info)
                VALUES (?, ?, ?, ?, ?)
            """, (conv_id, business_id, session_id, "[]", "{}"))
            conn.commit()
            
            return {
                "id": conv_id,
                "business_id": business_id,
                "session_id": session_id,
                "messages": [],
                "customer_info": {}
            }
    
    def save(
        self,
        conv_id: str,
        messages: list,
        customer_info: dict
    ):
        """Save conversation state."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversations 
                SET messages = ?, customer_info = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(messages),
                json.dumps(customer_info),
                self._now(),
                conv_id
            ))
            conn.commit()
    
    def get_history(self, business_id: str, session_id: str) -> dict:
        """Get chat history for a session."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT messages, customer_info FROM conversations WHERE business_id = ? AND session_id = ?",
                (business_id, session_id)
            )
            row = cursor.fetchone()
            
            if not row:
                return {"messages": [], "customer_info": {}}
            
            return {
                "messages": json.loads(row["messages"] or "[]"),
                "customer_info": json.loads(row["customer_info"] or "{}")
            }
    
    def delete_by_session(self, business_id: str, session_id: str) -> bool:
        """Delete a conversation by session ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM conversations WHERE business_id = ? AND session_id = ?",
                (business_id, session_id)
            )
            conn.commit()
            return cursor.rowcount > 0
