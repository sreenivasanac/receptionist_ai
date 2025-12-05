"""FAQ management API endpoints for V2."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.repositories import business_repo
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
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = business_repo.get_faqs(business_id)
    return {"faqs": faqs}


@router.post("/{business_id}/faqs")
async def add_faq(business_id: str, faq: FAQ):
    """Add a new FAQ to the business config."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = business_repo.get_faqs(business_id)
    faqs.append({"question": faq.question, "answer": faq.answer})
    
    business_repo.update_faqs(business_id, faqs)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQ added", "faqs": faqs}


@router.put("/{business_id}/faqs/{index}")
async def update_faq(business_id: str, index: int, faq: FAQ):
    """Update an existing FAQ by index."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = business_repo.get_faqs(business_id)
    
    if index < 0 or index >= len(faqs):
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    faqs[index] = {"question": faq.question, "answer": faq.answer}
    
    business_repo.update_faqs(business_id, faqs)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQ updated", "faq": faqs[index]}


@router.delete("/{business_id}/faqs/{index}")
async def delete_faq(business_id: str, index: int):
    """Delete an FAQ by index."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = business_repo.get_faqs(business_id)
    
    if index < 0 or index >= len(faqs):
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    deleted = faqs.pop(index)
    
    business_repo.update_faqs(business_id, faqs)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQ deleted", "deleted": deleted}


@router.put("/{business_id}/faqs")
async def replace_all_faqs(business_id: str, faq_list: FAQList):
    """Replace all FAQs for a business."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    faqs = [{"question": f.question, "answer": f.answer} for f in faq_list.faqs]
    
    business_repo.update_faqs(business_id, faqs)
    invalidate_agent_cache(business_id)
    
    return {"message": "FAQs updated", "count": len(faq_list.faqs)}
