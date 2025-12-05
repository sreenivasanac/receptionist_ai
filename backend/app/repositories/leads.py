"""Leads repository for data access."""
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.lead import Lead, LeadCreate, LeadUpdate


class LeadRepository(BaseRepository[Lead]):
    """Repository for lead data access."""
    
    table_name = "leads"
    
    def _row_to_model(self, row) -> Lead:
        """Convert a database row to a Lead model."""
        return Lead(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            interest=row["interest"],
            notes=row["notes"],
            company=row["company"],
            status=row["status"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list[Lead]:
        """Find leads for a business with optional status filter."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM leads WHERE business_id = ?"
            params = [business_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_by_email(self, business_id: str, email: str) -> Optional[Lead]:
        """Find a lead by email."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM leads WHERE business_id = ? AND email = ?",
                (business_id, email)
            )
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def create(self, business_id: str, data: LeadCreate) -> Lead:
        """Create a new lead."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            lead_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO leads 
                (id, business_id, name, email, phone, interest, notes, company, source, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """, (
                lead_id,
                business_id,
                data.name,
                data.email,
                data.phone,
                data.interest,
                data.notes,
                data.company,
                data.source,
                now,
                now
            ))
            conn.commit()
            
            return self.find_by_id_and_business(lead_id, business_id)
    
    def create_or_update(
        self,
        business_id: str,
        name: str,
        interest: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        notes: Optional[str] = None,
        company: Optional[str] = None,
        source: str = 'chatbot'
    ) -> tuple[str, bool]:
        """Create or update a lead. Returns (lead_id, is_new)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            if email:
                cursor.execute(
                    "SELECT id FROM leads WHERE business_id = ? AND email = ?",
                    (business_id, email)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE leads SET 
                            name = ?, interest = ?, phone = COALESCE(?, phone),
                            notes = COALESCE(?, notes), company = COALESCE(?, company),
                            updated_at = ?
                        WHERE id = ?
                    """, (name, interest, phone, notes, company, now, existing['id']))
                    conn.commit()
                    return existing['id'], False
            
            lead_id = self._generate_id()
            cursor.execute("""
                INSERT INTO leads 
                (id, business_id, name, email, phone, interest, notes, company, source, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """, (lead_id, business_id, name, email, phone, interest, notes, company, source, now, now))
            conn.commit()
            
            return lead_id, True
    
    def update(self, business_id: str, lead_id: str, data: LeadUpdate) -> Optional[Lead]:
        """Update a lead."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if data.name is not None:
                updates.append("name = ?")
                params.append(data.name)
            if data.email is not None:
                updates.append("email = ?")
                params.append(data.email)
            if data.phone is not None:
                updates.append("phone = ?")
                params.append(data.phone)
            if data.interest is not None:
                updates.append("interest = ?")
                params.append(data.interest)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)
            if data.company is not None:
                updates.append("company = ?")
                params.append(data.company)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status)
            
            if not updates:
                return self.find_by_id_and_business(lead_id, business_id)
            
            updates.append("updated_at = ?")
            params.append(self._now())
            params.extend([lead_id, business_id])
            
            cursor.execute(f"""
                UPDATE leads SET {', '.join(updates)}
                WHERE id = ? AND business_id = ?
            """, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_by_id_and_business(lead_id, business_id)
    
    def update_status(self, business_id: str, lead_id: str, status: str) -> bool:
        """Update lead status."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leads SET status = ?, updated_at = ?
                WHERE id = ? AND business_id = ?
            """, (status, self._now(), lead_id, business_id))
            conn.commit()
            return cursor.rowcount > 0
