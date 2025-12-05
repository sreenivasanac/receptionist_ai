"""Campaigns repository for data access."""
import json
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.campaign import Campaign, CampaignCreate, CampaignUpdate


class CampaignRepository(BaseRepository[Campaign]):
    """Repository for SMS campaign data access."""
    
    table_name = "sms_campaigns"
    
    def _row_to_model(self, row) -> Campaign:
        """Convert a database row to a Campaign model."""
        return Campaign(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            message=row["message"],
            recipient_filter=json.loads(row["recipient_filter"] or "{}"),
            recipient_count=row["recipient_count"],
            status=row["status"],
            scheduled_at=row["scheduled_at"],
            sent_at=row["sent_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list[Campaign]:
        """Find campaigns for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM sms_campaigns WHERE business_id = ?"
            params = [business_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def create(
        self,
        business_id: str,
        data: CampaignCreate,
        recipient_count: int
    ) -> Campaign:
        """Create a new campaign."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            campaign_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO sms_campaigns 
                (id, business_id, name, message, recipient_filter, recipient_count, status, scheduled_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
            """, (
                campaign_id,
                business_id,
                data.name,
                data.message,
                json.dumps(data.recipient_filter.model_dump()),
                recipient_count,
                data.scheduled_at,
                now,
                now
            ))
            conn.commit()
            
            return self.find_by_id_and_business(campaign_id, business_id)
    
    def update(
        self,
        business_id: str,
        campaign_id: str,
        data: CampaignUpdate,
        recipient_count: Optional[int] = None
    ) -> Optional[Campaign]:
        """Update a campaign."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if data.name is not None:
                updates.append("name = ?")
                params.append(data.name)
            if data.message is not None:
                updates.append("message = ?")
                params.append(data.message)
            if data.recipient_filter is not None:
                updates.append("recipient_filter = ?")
                params.append(json.dumps(data.recipient_filter.model_dump()))
            if recipient_count is not None:
                updates.append("recipient_count = ?")
                params.append(recipient_count)
            if data.scheduled_at is not None:
                updates.append("scheduled_at = ?")
                params.append(data.scheduled_at)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status)
            
            if not updates:
                return self.find_by_id_and_business(campaign_id, business_id)
            
            updates.append("updated_at = ?")
            params.append(self._now())
            params.extend([campaign_id, business_id])
            
            cursor.execute(f"""
                UPDATE sms_campaigns SET {', '.join(updates)}
                WHERE id = ? AND business_id = ?
            """, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_by_id_and_business(campaign_id, business_id)
    
    def mark_sent(self, campaign_id: str) -> bool:
        """Mark a campaign as sent."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            cursor.execute("""
                UPDATE sms_campaigns SET status = 'sent', sent_at = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, campaign_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_status(self, business_id: str, campaign_id: str) -> Optional[str]:
        """Get campaign status."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status FROM sms_campaigns WHERE id = ? AND business_id = ?",
                (campaign_id, business_id)
            )
            row = cursor.fetchone()
            return row["status"] if row else None
    
    def get_recipient_filter(self, business_id: str, campaign_id: str) -> Optional[dict]:
        """Get campaign recipient filter."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT recipient_filter FROM sms_campaigns WHERE id = ? AND business_id = ?",
                (campaign_id, business_id)
            )
            row = cursor.fetchone()
            return json.loads(row["recipient_filter"] or "{}") if row else None
