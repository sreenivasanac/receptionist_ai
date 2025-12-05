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
    
    # V3 Methods
    
    def search(
        self,
        business_id: str,
        query: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """Search conversations with filters."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT * FROM conversations WHERE business_id = ?"
            params = [business_id]
            
            if start_date:
                sql += " AND date(created_at) >= ?"
                params.append(start_date)
            
            if end_date:
                sql += " AND date(created_at) <= ?"
                params.append(end_date)
            
            if query:
                sql += " AND (messages LIKE ? OR customer_info LIKE ?)"
                search_pattern = f"%{query}%"
                params.extend([search_pattern, search_pattern])
            
            sql += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                conv = self._row_to_model(row)
                messages = conv["messages"]
                conv["message_count"] = len(messages)
                conv["preview"] = messages[0]["content"][:100] if messages else ""
                conv["last_message"] = messages[-1]["content"][:100] if messages else ""
                results.append(conv)
            
            return results
    
    def count_search(
        self,
        business_id: str,
        query: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """Count conversations matching search criteria."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            sql = "SELECT COUNT(*) as count FROM conversations WHERE business_id = ?"
            params = [business_id]
            
            if start_date:
                sql += " AND date(created_at) >= ?"
                params.append(start_date)
            
            if end_date:
                sql += " AND date(created_at) <= ?"
                params.append(end_date)
            
            if query:
                sql += " AND (messages LIKE ? OR customer_info LIKE ?)"
                search_pattern = f"%{query}%"
                params.extend([search_pattern, search_pattern])
            
            cursor.execute(sql, params)
            return cursor.fetchone()["count"]
    
    def export(
        self,
        business_id: str,
        session_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = "json"
    ) -> list[dict]:
        """Export conversations for download."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute(
                    "SELECT * FROM conversations WHERE business_id = ? AND session_id = ?",
                    (business_id, session_id)
                )
            else:
                sql = "SELECT * FROM conversations WHERE business_id = ?"
                params = [business_id]
                
                if start_date:
                    sql += " AND date(created_at) >= ?"
                    params.append(start_date)
                
                if end_date:
                    sql += " AND date(created_at) <= ?"
                    params.append(end_date)
                
                sql += " ORDER BY created_at DESC"
                cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            
            if format == "csv":
                results = []
                for row in rows:
                    conv = self._row_to_model(row)
                    for msg in conv["messages"]:
                        results.append({
                            "session_id": conv["session_id"],
                            "timestamp": msg.get("timestamp", ""),
                            "role": msg.get("role", ""),
                            "content": msg.get("content", ""),
                            "customer_name": conv["customer_info"].get("first_name", ""),
                            "customer_phone": conv["customer_info"].get("phone", ""),
                            "customer_email": conv["customer_info"].get("email", "")
                        })
                return results
            else:
                return [self._row_to_model(row) for row in rows]
    
    def get_summary(self, business_id: str, session_id: str) -> dict:
        """Get a summary of a conversation."""
        conv = self.find_by_session(business_id, session_id)
        if not conv:
            return {}
        
        messages = conv["messages"]
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "customer_info": conv["customer_info"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "duration_estimate": self._estimate_duration(messages)
        }
    
    def _estimate_duration(self, messages: list) -> str:
        """Estimate conversation duration from timestamps."""
        if len(messages) < 2:
            return "< 1 min"
        
        try:
            from datetime import datetime
            first = datetime.fromisoformat(messages[0].get("timestamp", ""))
            last = datetime.fromisoformat(messages[-1].get("timestamp", ""))
            diff = (last - first).total_seconds() / 60
            if diff < 1:
                return "< 1 min"
            elif diff < 60:
                return f"{int(diff)} min"
            else:
                return f"{int(diff / 60)}h {int(diff % 60)}m"
        except:
            return "unknown"
