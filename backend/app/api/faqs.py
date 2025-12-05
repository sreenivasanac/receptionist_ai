"""FAQ management API endpoints."""
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Body
import yaml

from app.repositories import business_repo
from app.api.chat import invalidate_agent_cache

router = APIRouter(prefix="/admin", tags=["FAQs"])


class FAQItem(BaseModel):
    """FAQ item model."""
    question: str
    answer: str


class FAQCreate(BaseModel):
    """Create FAQ request."""
    question: str
    answer: str


class FAQUpdate(BaseModel):
    """Update FAQ request."""
    question: Optional[str] = None
    answer: Optional[str] = None


@router.get("/{business_id}/faqs", response_model=list[FAQItem])
async def list_faqs(business_id: str):
    """List all FAQs for a business."""
    config = business_repo.get_config(business_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = config.get('faqs', [])
    return [FAQItem(question=f.get('question', ''), answer=f.get('answer', '')) for f in faqs]


@router.post("/{business_id}/faqs", response_model=FAQItem)
async def create_faq(business_id: str, faq: FAQCreate):
    """Add a new FAQ."""
    config = business_repo.get_config(business_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = config.get('faqs', [])
    new_faq = {'question': faq.question, 'answer': faq.answer}
    faqs.append(new_faq)
    config['faqs'] = faqs
    
    config_yaml = yaml.dump(config, default_flow_style=False)
    business_repo.update_config_yaml(business_id, config_yaml)
    invalidate_agent_cache(business_id)
    
    return FAQItem(question=faq.question, answer=faq.answer)


@router.put("/{business_id}/faqs/{faq_index}", response_model=FAQItem)
async def update_faq(business_id: str, faq_index: int, faq: FAQUpdate):
    """Update an existing FAQ by index."""
    config = business_repo.get_config(business_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = config.get('faqs', [])
    if faq_index < 0 or faq_index >= len(faqs):
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    if faq.question is not None:
        faqs[faq_index]['question'] = faq.question
    if faq.answer is not None:
        faqs[faq_index]['answer'] = faq.answer
    
    config['faqs'] = faqs
    config_yaml = yaml.dump(config, default_flow_style=False)
    business_repo.update_config_yaml(business_id, config_yaml)
    invalidate_agent_cache(business_id)
    
    return FAQItem(question=faqs[faq_index]['question'], answer=faqs[faq_index]['answer'])


@router.delete("/{business_id}/faqs/{faq_index}")
async def delete_faq(business_id: str, faq_index: int):
    """Delete an FAQ by index."""
    config = business_repo.get_config(business_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = config.get('faqs', [])
    if faq_index < 0 or faq_index >= len(faqs):
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    deleted = faqs.pop(faq_index)
    config['faqs'] = faqs
    config_yaml = yaml.dump(config, default_flow_style=False)
    business_repo.update_config_yaml(business_id, config_yaml)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQ deleted", "deleted": deleted}


@router.post("/{business_id}/faqs/reorder")
async def reorder_faqs(business_id: str, new_order: list[int] = Body(...)):
    """Reorder FAQs. Provide list of current indices in new order."""
    config = business_repo.get_config(business_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = config.get('faqs', [])
    
    if len(new_order) != len(faqs):
        raise HTTPException(status_code=400, detail="New order must include all FAQ indices")
    
    if set(new_order) != set(range(len(faqs))):
        raise HTTPException(status_code=400, detail="Invalid indices in new order")
    
    reordered = [faqs[i] for i in new_order]
    config['faqs'] = reordered
    config_yaml = yaml.dump(config, default_flow_style=False)
    business_repo.update_config_yaml(business_id, config_yaml)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQs reordered", "faqs": reordered}
