"""Website scraper API endpoints for extracting business information."""
import uuid
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Body
import yaml

from app.repositories import business_repo
from app.services.scraper import scrape_website, save_scraped_content
from app.services.llm_extractor import extract_with_llm_safe
from app.api.chat import invalidate_agent_cache

router = APIRouter(prefix="/business", tags=["Scraper"])


class ScrapeRequest(BaseModel):
    """Request model for scraping URLs."""
    urls: List[str]


class ScrapeResult(BaseModel):
    """Result of scraping a single URL."""
    url: str
    success: bool
    error: Optional[str] = None
    title: Optional[str] = None


class FieldDiff(BaseModel):
    """Comparison of current vs extracted value for a field."""
    field: str
    field_label: str
    current_value: Optional[str] = None
    extracted_value: Optional[str] = None


class ExtractedServiceItem(BaseModel):
    """Service extracted from website."""
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    is_new: bool = True


class ExtractedFAQItem(BaseModel):
    """FAQ extracted from website."""
    question: str
    answer: str
    is_new: bool = True


class ExtractedHoursItem(BaseModel):
    """Business hours for a day."""
    day: str
    open: Optional[str] = None
    close: Optional[str] = None
    closed: bool = False


class ScrapeResponse(BaseModel):
    """Response model for scraping with LLM extraction."""
    results: List[ScrapeResult]
    current_config: dict
    extracted_config: dict
    field_diffs: List[FieldDiff]
    new_services: List[ExtractedServiceItem]
    new_faqs: List[ExtractedFAQItem]
    extracted_hours: List[ExtractedHoursItem]
    extraction_error: Optional[str] = None


@router.post("/{business_id}/scrape", response_model=ScrapeResponse)
async def scrape_urls(business_id: str, request: ScrapeRequest):
    """
    Scrape multiple URLs and extract business information using LLM.
    Returns current config, extracted config, and field-by-field diff.
    """
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    if len(request.urls) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 URLs allowed")
    
    # Get current business config
    current_config = business_repo.get_config(business_id) or {}
    
    # Scrape all URLs and combine content
    results = []
    combined_content = []
    
    for url in request.urls:
        scraped = await scrape_website(url)
        
        if scraped.get("success"):
            results.append(ScrapeResult(
                url=url,
                success=True,
                title=scraped.get("title", "")
            ))
            await save_scraped_content(business_id, url, scraped)
            combined_content.append(scraped.get("raw_content", ""))
        else:
            results.append(ScrapeResult(
                url=url,
                success=False,
                error=scraped.get("error", "Unknown error")
            ))
    
    # Extract using LLM
    extraction_error = None
    extracted_config = {}
    
    if combined_content:
        full_content = "\n\n---PAGE BREAK---\n\n".join(combined_content)
        llm_result, error = extract_with_llm_safe(full_content)
        
        if error:
            extraction_error = error
        elif llm_result:
            extracted_config = llm_result.model_dump(exclude_none=True)
    
    # Build field diffs for simple fields
    simple_fields = [
        ("name", "Business Name"),
        ("phone", "Phone"),
        ("email", "Email"),
        ("location", "Address"),
    ]
    
    field_diffs = []
    for field, label in simple_fields:
        current_val = current_config.get(field)
        extracted_val = extracted_config.get(field)
        if current_val or extracted_val:
            field_diffs.append(FieldDiff(
                field=field,
                field_label=label,
                current_value=str(current_val) if current_val else None,
                extracted_value=str(extracted_val) if extracted_val else None
            ))
    
    # Add policy diffs
    current_policies = current_config.get("policies", {})
    extracted_policies = extracted_config.get("policies", {})
    policy_fields = [
        ("cancellation", "Cancellation Policy"),
        ("walk_ins", "Walk-in Policy"),
    ]
    for field, label in policy_fields:
        current_val = current_policies.get(field) if isinstance(current_policies, dict) else None
        extracted_val = extracted_policies.get(field) if isinstance(extracted_policies, dict) else None
        if current_val or extracted_val:
            field_diffs.append(FieldDiff(
                field=f"policies.{field}",
                field_label=label,
                current_value=str(current_val) if current_val else None,
                extracted_value=str(extracted_val) if extracted_val else None
            ))
    
    # Find new services (not in current config)
    current_service_names = {s.get("name", "").lower() for s in current_config.get("services", [])}
    new_services = []
    for svc in extracted_config.get("services", []):
        is_new = svc.get("name", "").lower() not in current_service_names
        new_services.append(ExtractedServiceItem(
            name=svc.get("name", ""),
            description=svc.get("description"),
            duration_minutes=svc.get("duration_minutes"),
            price=svc.get("price"),
            is_new=is_new
        ))
    
    # Find new FAQs (not in current config)
    current_faq_questions = {f.get("question", "").lower() for f in current_config.get("faqs", [])}
    new_faqs = []
    for faq in extracted_config.get("faqs", []):
        is_new = faq.get("question", "").lower() not in current_faq_questions
        new_faqs.append(ExtractedFAQItem(
            question=faq.get("question", ""),
            answer=faq.get("answer", ""),
            is_new=is_new
        ))
    
    # Extract hours
    extracted_hours = []
    days_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    hours_data = extracted_config.get("hours", {})
    if hours_data:
        for day in days_order:
            day_hours = hours_data.get(day, {})
            if day_hours:
                extracted_hours.append(ExtractedHoursItem(
                    day=day,
                    open=day_hours.get("open"),
                    close=day_hours.get("close"),
                    closed=day_hours.get("closed", False)
                ))
    
    return ScrapeResponse(
        results=results,
        current_config=current_config,
        extracted_config=extracted_config,
        field_diffs=field_diffs,
        new_services=new_services,
        new_faqs=new_faqs,
        extracted_hours=extracted_hours,
        extraction_error=extraction_error
    )


class ApplyExtractedRequest(BaseModel):
    """Request model for applying extracted information."""
    selected_fields: dict[str, str]  # field -> "current" | "extracted"
    extracted_values: dict[str, str]  # field -> extracted value
    add_services: List[dict]
    add_faqs: List[dict]
    apply_hours: bool = False
    extracted_hours: Optional[dict] = None


@router.post("/{business_id}/scrape/apply", response_model=dict)
async def apply_extracted_info(
    business_id: str,
    request: ApplyExtractedRequest
):
    """
    Apply selected extracted information to business config.
    Allows user to choose which fields to update and which services/FAQs to add.
    """
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    config = business_repo.get_config(business_id) or {}
    updated_fields = []
    
    # Apply field selections
    for field, choice in request.selected_fields.items():
        if choice == "extracted" and field in request.extracted_values:
            extracted_val = request.extracted_values[field]
            if "." in field:
                # Nested field like policies.cancellation
                parts = field.split(".")
                if parts[0] not in config:
                    config[parts[0]] = {}
                config[parts[0]][parts[1]] = extracted_val
            else:
                config[field] = extracted_val
            updated_fields.append(field)
    
    # Add new services (avoid duplicates by name)
    if request.add_services:
        existing_names = {s.get("name", "").lower() for s in config.get("services", [])}
        if "services" not in config:
            config["services"] = []
        for svc in request.add_services:
            if svc.get("name", "").lower() not in existing_names:
                # Generate ID for new service
                svc_id = svc.get("name", "service").lower().replace(" ", "_")
                config["services"].append({
                    "id": svc_id,
                    "name": svc.get("name", ""),
                    "description": svc.get("description", ""),
                    "duration_minutes": svc.get("duration_minutes", 30),
                    "price": svc.get("price", 0)
                })
                existing_names.add(svc.get("name", "").lower())
        updated_fields.append(f"services (+{len(request.add_services)})")
    
    # Add new FAQs (avoid duplicates by question)
    if request.add_faqs:
        existing_questions = {f.get("question", "").lower() for f in config.get("faqs", [])}
        if "faqs" not in config:
            config["faqs"] = []
        for faq in request.add_faqs:
            if faq.get("question", "").lower() not in existing_questions:
                config["faqs"].append({
                    "question": faq.get("question", ""),
                    "answer": faq.get("answer", "")
                })
                existing_questions.add(faq.get("question", "").lower())
        updated_fields.append(f"faqs (+{len(request.add_faqs)})")
    
    # Apply hours if selected
    if request.apply_hours and request.extracted_hours:
        if "hours" not in config:
            config["hours"] = {}
        for day, hours in request.extracted_hours.items():
            if hours:
                config["hours"][day] = hours
        updated_fields.append("hours")
    
    # Save updated config
    config_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
    business_repo.update_config_yaml(business_id, config_yaml)
    invalidate_agent_cache(business_id)
    
    return {
        "message": "Configuration updated with extracted information",
        "updated_fields": updated_fields
    }
