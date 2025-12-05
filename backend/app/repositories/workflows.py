"""Workflows repository for V3 custom workflow builder."""
import json
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository


class TriggerConfig(BaseModel):
    """Configuration for workflow triggers."""
    keywords: list[str] = Field(default_factory=list)
    segment: Optional[str] = None
    customer_type: Optional[str] = None
    time_condition: Optional[str] = None
    idle_minutes: Optional[int] = None


class WorkflowAction(BaseModel):
    """Single action in a workflow."""
    type: str
    config: dict = Field(default_factory=dict)


class Workflow(BaseModel):
    """Workflow model."""
    id: str
    business_id: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: TriggerConfig = Field(default_factory=TriggerConfig)
    actions: list[WorkflowAction] = Field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: dict = Field(default_factory=dict)
    actions: list[dict] = Field(default_factory=list)
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None
    actions: Optional[list[dict]] = None
    is_active: Optional[bool] = None


WORKFLOW_TEMPLATES = [
    {
        "name": "Birthday Discount",
        "description": "Offer special discount when customer mentions birthday",
        "trigger_type": "keyword",
        "trigger_config": {"keywords": ["birthday", "bday", "born"]},
        "actions": [
            {"type": "send_message", "config": {"message": "Happy Birthday! 🎂 We'd love to celebrate with you - enjoy 20% off your next service!"}},
            {"type": "apply_discount", "config": {"percent": 20, "reason": "birthday"}}
        ]
    },
    {
        "name": "Bridal Inquiry Capture",
        "description": "Capture leads for wedding/bridal inquiries",
        "trigger_type": "keyword",
        "trigger_config": {"keywords": ["wedding", "bridal", "bride", "engagement", "bachelorette"]},
        "actions": [
            {"type": "capture_lead", "config": {"interest": "bridal_package"}},
            {"type": "send_message", "config": {"message": "Congratulations! We'd love to help make your special day even more beautiful. Let me connect you with our bridal specialist."}}
        ]
    },
    {
        "name": "New Customer Welcome",
        "description": "Special offer for first-time customers",
        "trigger_type": "segment",
        "trigger_config": {"customer_type": "new"},
        "actions": [
            {"type": "send_message", "config": {"message": "Welcome! As a new client, enjoy 15% off your first visit with us."}},
            {"type": "apply_discount", "config": {"percent": 15, "reason": "new_customer"}}
        ]
    },
    {
        "name": "Corporate Inquiry Routing",
        "description": "Capture corporate and group booking inquiries",
        "trigger_type": "keyword",
        "trigger_config": {"keywords": ["corporate", "company", "team", "group booking", "employees", "office"]},
        "actions": [
            {"type": "capture_lead", "config": {"interest": "corporate_wellness"}},
            {"type": "send_message", "config": {"message": "We'd love to discuss corporate packages for your team! Let me get your details so our partnerships team can reach out."}}
        ]
    },
    {
        "name": "Membership Inquiry",
        "description": "Handle membership and package inquiries",
        "trigger_type": "keyword",
        "trigger_config": {"keywords": ["membership", "package", "subscription", "monthly plan", "unlimited"]},
        "actions": [
            {"type": "capture_lead", "config": {"interest": "membership"}},
            {"type": "offer_service", "config": {"service_type": "membership"}}
        ]
    },
    {
        "name": "Loyalty Reminder",
        "description": "Remind returning customers of their loyalty status",
        "trigger_type": "segment",
        "trigger_config": {"customer_type": "returning", "min_visits": 5},
        "actions": [
            {"type": "send_message", "config": {"message": "Thank you for being a loyal customer! As a VIP, you're eligible for our exclusive rewards."}}
        ]
    }
]


class WorkflowRepository(BaseRepository):
    """Repository for workflow data access."""
    
    table_name = "workflows"
    
    def _row_to_model(self, row) -> Workflow:
        """Convert a database row to a Workflow model."""
        return Workflow(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            description=row["description"],
            trigger_type=row["trigger_type"],
            trigger_config=TriggerConfig(**json.loads(row["trigger_config"] or "{}")),
            actions=[WorkflowAction(**a) for a in json.loads(row["actions"] or "[]")],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def create(self, business_id: str, data: WorkflowCreate) -> str:
        """Create a new workflow."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            workflow_id = self._generate_id()
            
            cursor.execute("""
                INSERT INTO workflows (id, business_id, name, description, trigger_type, trigger_config, actions, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_id,
                business_id,
                data.name,
                data.description,
                data.trigger_type,
                json.dumps(data.trigger_config),
                json.dumps(data.actions),
                1 if data.is_active else 0
            ))
            conn.commit()
            return workflow_id
    
    def update(self, business_id: str, workflow_id: str, data: WorkflowUpdate) -> bool:
        """Update a workflow."""
        existing = self.find_by_id_and_business(workflow_id, business_id)
        if not existing:
            return False
        
        updates = []
        params = []
        
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.trigger_type is not None:
            updates.append("trigger_type = ?")
            params.append(data.trigger_type)
        if data.trigger_config is not None:
            updates.append("trigger_config = ?")
            params.append(json.dumps(data.trigger_config))
        if data.actions is not None:
            updates.append("actions = ?")
            params.append(json.dumps(data.actions))
        if data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)
        
        if not updates:
            return True
        
        updates.append("updated_at = ?")
        params.append(self._now())
        params.extend([workflow_id, business_id])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE workflows SET {', '.join(updates)} WHERE id = ? AND business_id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def find_active_by_business(self, business_id: str) -> list[Workflow]:
        """Find all active workflows for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workflows WHERE business_id = ? AND is_active = 1 ORDER BY created_at DESC",
                (business_id,)
            )
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_by_trigger_type(self, business_id: str, trigger_type: str) -> list[Workflow]:
        """Find active workflows by trigger type."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workflows WHERE business_id = ? AND trigger_type = ? AND is_active = 1",
                (business_id, trigger_type)
            )
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def toggle_active(self, business_id: str, workflow_id: str) -> Optional[bool]:
        """Toggle workflow active status. Returns new status or None if not found."""
        workflow = self.find_by_id_and_business(workflow_id, business_id)
        if not workflow:
            return None
        
        new_status = not workflow.is_active
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE workflows SET is_active = ?, updated_at = ? WHERE id = ? AND business_id = ?",
                (1 if new_status else 0, self._now(), workflow_id, business_id)
            )
            conn.commit()
            return new_status
    
    def get_templates(self) -> list[dict]:
        """Get pre-built workflow templates."""
        return WORKFLOW_TEMPLATES
    
    def create_from_template(self, business_id: str, template_name: str) -> Optional[str]:
        """Create a workflow from a template."""
        template = next((t for t in WORKFLOW_TEMPLATES if t["name"] == template_name), None)
        if not template:
            return None
        
        data = WorkflowCreate(**template)
        return self.create(business_id, data)


workflow_repo = WorkflowRepository()
