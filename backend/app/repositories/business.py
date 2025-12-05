"""Business repository for data access."""
import json
from typing import Optional

import yaml

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.business import Business, BusinessUpdate


class BusinessRepository(BaseRepository[Business]):
    """Repository for business data access."""
    
    table_name = "businesses"
    
    def _row_to_model(self, row) -> Business:
        """Convert a database row to a Business model."""
        return Business(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            address=row["address"],
            phone=row["phone"],
            email=row["email"],
            website=row["website"],
            config_yaml=row["config_yaml"],
            features_enabled=json.loads(row["features_enabled"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_id(self, id: str) -> Optional[Business]:
        """Find a business by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses WHERE id = ?", (id,))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def get_config_yaml(self, business_id: str) -> Optional[str]:
        """Get business config YAML."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT config_yaml FROM businesses WHERE id = ?", (business_id,))
            row = cursor.fetchone()
            return row["config_yaml"] if row else None
    
    def get_config(self, business_id: str) -> Optional[dict]:
        """Get parsed business config."""
        config_yaml = self.get_config_yaml(business_id)
        if not config_yaml:
            return None
        try:
            return yaml.safe_load(config_yaml)
        except yaml.YAMLError:
            return None
    
    def get_basic_info(self, business_id: str) -> Optional[dict]:
        """Get basic business info for agent creation."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, type, config_yaml FROM businesses WHERE id = ?",
                (business_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "name": row["name"],
                "type": row["type"],
                "config_yaml": row["config_yaml"]
            }
    
    def get_features(self, business_id: str) -> dict:
        """Get enabled features for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT features_enabled FROM businesses WHERE id = ?", (business_id,))
            row = cursor.fetchone()
            return json.loads(row["features_enabled"] or "{}") if row else {}
    
    def create(
        self,
        business_id: str,
        name: str,
        business_type: str,
        config_yaml: str,
        features_enabled: dict
    ) -> str:
        """Create a new business and return the ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO businesses (id, name, type, config_yaml, features_enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                business_id,
                name,
                business_type,
                config_yaml,
                json.dumps(features_enabled)
            ))
            conn.commit()
            return business_id
    
    def update(self, business_id: str, update: BusinessUpdate) -> Optional[Business]:
        """Update a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            values = []
            
            if update.name is not None:
                updates.append("name = ?")
                values.append(update.name)
            if update.address is not None:
                updates.append("address = ?")
                values.append(update.address)
            if update.phone is not None:
                updates.append("phone = ?")
                values.append(update.phone)
            if update.email is not None:
                updates.append("email = ?")
                values.append(update.email)
            if update.website is not None:
                updates.append("website = ?")
                values.append(update.website)
            if update.config_yaml is not None:
                updates.append("config_yaml = ?")
                values.append(update.config_yaml)
            if update.features_enabled is not None:
                updates.append("features_enabled = ?")
                values.append(json.dumps(update.features_enabled))
            
            if not updates:
                return self.find_by_id(business_id)
            
            updates.append("updated_at = ?")
            values.append(self._now())
            values.append(business_id)
            
            cursor.execute(
                f"UPDATE businesses SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_by_id(business_id)
    
    def update_config_yaml(self, business_id: str, config_yaml: str) -> bool:
        """Update business config YAML."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE businesses 
                SET config_yaml = ?, updated_at = ?
                WHERE id = ?
            """, (config_yaml, self._now(), business_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_features(self, business_id: str, features: dict) -> bool:
        """Update business features."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE businesses 
                SET features_enabled = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(features), self._now(), business_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_faqs(self, business_id: str, faqs: list[dict]) -> bool:
        """Update FAQs in business config."""
        config = self.get_config(business_id) or {}
        config["faqs"] = faqs
        new_yaml = yaml.dump(config, default_flow_style=False)
        return self.update_config_yaml(business_id, new_yaml)
    
    def get_faqs(self, business_id: str) -> list[dict]:
        """Get FAQs from business config."""
        config = self.get_config(business_id)
        if not config:
            return []
        return config.get("faqs", [])
