"""FAQ management API endpoints for V2."""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml

from app.db.database import get_db_connection
from app.api.chat import invalidate_agent_cache

router = APIRouter(prefix="/admin", tags=["FAQs"])


class FAQ(BaseModel):
    """FAQ item."""
    question: str
    answer: str


class FAQList(BaseModel):
    """List of FAQs."""
    faqs: list[FAQ]


@router.get("/{business_id}/faqs")
async def list_faqs(business_id: str):
    """Get all FAQs for a business from its config."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"]
        if not config_yaml:
            return {"faqs": []}
        
        try:
            config = yaml.safe_load(config_yaml) or {}
            faqs = config.get("faqs", [])
            return {"faqs": faqs}
        except yaml.YAMLError:
            return {"faqs": []}


@router.post("/{business_id}/faqs")
async def add_faq(business_id: str, faq: FAQ):
    """Add a new FAQ to the business config."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"] or ""
        try:
            config = yaml.safe_load(config_yaml) or {}
        except yaml.YAMLError:
            config = {}
        
        if "faqs" not in config:
            config["faqs"] = []
        
        config["faqs"].append({
            "question": faq.question,
            "answer": faq.answer
        })
        
        new_yaml = yaml.dump(config, default_flow_style=False)
        cursor.execute("""
            UPDATE businesses SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (new_yaml, datetime.now().isoformat(), business_id))
        conn.commit()
        
        invalidate_agent_cache(business_id)
        
        return {"message": "FAQ added", "faqs": config["faqs"]}


@router.put("/{business_id}/faqs/{index}")
async def update_faq(business_id: str, index: int, faq: FAQ):
    """Update an existing FAQ by index."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"] or ""
        try:
            config = yaml.safe_load(config_yaml) or {}
        except yaml.YAMLError:
            config = {}
        
        faqs = config.get("faqs", [])
        if index < 0 or index >= len(faqs):
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        faqs[index] = {
            "question": faq.question,
            "answer": faq.answer
        }
        config["faqs"] = faqs
        
        new_yaml = yaml.dump(config, default_flow_style=False)
        cursor.execute("""
            UPDATE businesses SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (new_yaml, datetime.now().isoformat(), business_id))
        conn.commit()
        
        invalidate_agent_cache(business_id)
        
        return {"message": "FAQ updated", "faq": faqs[index]}


@router.delete("/{business_id}/faqs/{index}")
async def delete_faq(business_id: str, index: int):
    """Delete an FAQ by index."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"] or ""
        try:
            config = yaml.safe_load(config_yaml) or {}
        except yaml.YAMLError:
            config = {}
        
        faqs = config.get("faqs", [])
        if index < 0 or index >= len(faqs):
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        deleted = faqs.pop(index)
        config["faqs"] = faqs
        
        new_yaml = yaml.dump(config, default_flow_style=False)
        cursor.execute("""
            UPDATE businesses SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (new_yaml, datetime.now().isoformat(), business_id))
        conn.commit()
        
        invalidate_agent_cache(business_id)
        
        return {"message": "FAQ deleted", "deleted": deleted}


@router.put("/{business_id}/faqs")
async def replace_all_faqs(business_id: str, faq_list: FAQList):
    """Replace all FAQs for a business."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config_yaml = biz["config_yaml"] or ""
        try:
            config = yaml.safe_load(config_yaml) or {}
        except yaml.YAMLError:
            config = {}
        
        config["faqs"] = [{"question": f.question, "answer": f.answer} for f in faq_list.faqs]
        
        new_yaml = yaml.dump(config, default_flow_style=False)
        cursor.execute("""
            UPDATE businesses SET config_yaml = ?, updated_at = ?
            WHERE id = ?
        """, (new_yaml, datetime.now().isoformat(), business_id))
        conn.commit()
        
        invalidate_agent_cache(business_id)
        
        return {"message": "FAQs updated", "count": len(faq_list.faqs)}
