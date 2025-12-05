"""Business configuration API endpoints."""
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import yaml

from app.db.database import get_db_connection
from app.models.business import Business, BusinessCreate, BusinessUpdate, BusinessConfig

router = APIRouter(prefix="/business", tags=["Business"])


@router.get("/{business_id}", response_model=Business)
async def get_business(business_id: str):
    """Get business by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return Business(
            id=biz["id"],
            name=biz["name"],
            type=biz["type"],
            address=biz["address"],
            phone=biz["phone"],
            email=biz["email"],
            website=biz["website"],
            config_yaml=biz["config_yaml"],
            features_enabled=json.loads(biz["features_enabled"] or "{}"),
            created_at=biz["created_at"],
            updated_at=biz["updated_at"]
        )


@router.put("/{business_id}", response_model=Business)
async def update_business(business_id: str, update: BusinessUpdate):
    """Update business details."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
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
        
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(business_id)
            
            cursor.execute(
                f"UPDATE businesses SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
        
        return await get_business(business_id)


@router.get("/{business_id}/config", response_model=dict)
async def get_business_config(business_id: str):
    """Get parsed business configuration."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT config_yaml FROM businesses WHERE id = ?", (business_id,))
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"]
        if not config_yaml:
            return {"config": {}, "message": "No configuration set"}
        
        try:
            config = yaml.safe_load(config_yaml)
            return {"config": config}
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML configuration: {e}")


@router.put("/{business_id}/config", response_model=dict)
async def update_business_config(business_id: str, config: dict):
    """Update business configuration from parsed dict (converts to YAML)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
        try:
            config_yaml = yaml.dump(config, default_flow_style=False)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")
        
        cursor.execute("""
            UPDATE businesses 
            SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (config_yaml, datetime.now().isoformat(), business_id))
        conn.commit()
        
        return {"message": "Configuration updated", "config": config}


@router.put("/{business_id}/config/yaml", response_model=dict)
async def update_business_config_yaml(business_id: str, yaml_content: str):
    """Update business configuration from raw YAML string."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
        
        cursor.execute("""
            UPDATE businesses 
            SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (yaml_content, datetime.now().isoformat(), business_id))
        conn.commit()
        
        return {"message": "Configuration updated"}


@router.get("/{business_id}/features", response_model=dict)
async def get_features(business_id: str):
    """Get enabled features for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT features_enabled FROM businesses WHERE id = ?", (business_id,))
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return {"features": json.loads(biz["features_enabled"] or "{}")}


@router.put("/{business_id}/features", response_model=dict)
async def update_features(business_id: str, features: dict):
    """Update enabled features for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM businesses WHERE id = ?", (business_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Business not found")
        
        cursor.execute("""
            UPDATE businesses 
            SET features_enabled = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(features), datetime.now().isoformat(), business_id))
        conn.commit()
        
        return {"message": "Features updated", "features": features}


@router.get("/{business_id}/embed-code", response_model=dict)
async def get_embed_code(business_id: str, base_url: Optional[str] = Query(default="https://widget.localkeystone.com")):
    """Get the embed code for the chat widget."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM businesses WHERE id = ?", (business_id,))
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        embed_code = f'''<script src="{base_url}/chat.js" data-business-id="{business_id}"></script>'''
        
        return {
            "business_id": business_id,
            "business_name": biz["name"],
            "embed_code": embed_code,
            "instructions": "Add this script tag to your website's HTML, preferably before the closing </body> tag."
        }
