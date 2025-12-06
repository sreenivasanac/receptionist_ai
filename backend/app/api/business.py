"""Business configuration API endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Body
import yaml

from app.repositories import business_repo, service_repo
from app.models.business import Business, BusinessUpdate
from app.api.chat import invalidate_agent_cache

router = APIRouter(prefix="/business", tags=["Business"])


@router.get("/{business_id}", response_model=Business)
async def get_business(business_id: str):
    """Get business by ID."""
    business = business_repo.find_by_id(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.put("/{business_id}", response_model=Business)
async def update_business(business_id: str, update: BusinessUpdate):
    """Update business details."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    business = business_repo.update(business_id, update)
    
    if update.config_yaml is not None:
        try:
            config = yaml.safe_load(update.config_yaml)
            services = config.get('services', [])
            service_repo.sync_from_config(business_id, services)
        except yaml.YAMLError:
            pass
        invalidate_agent_cache(business_id)
    
    return business


@router.get("/{business_id}/config", response_model=dict)
async def get_business_config(business_id: str):
    """Get parsed business configuration."""
    config = business_repo.get_config(business_id)
    
    if config is None:
        config_yaml = business_repo.get_config_yaml(business_id)
        if config_yaml is None:
            raise HTTPException(status_code=404, detail="Business not found")
        return {"config": {}, "message": "No configuration set"}
    
    return {"config": config}


@router.put("/{business_id}/config", response_model=dict)
async def update_business_config(business_id: str, config: dict = Body(...)):
    """Update business configuration from parsed dict (converts to YAML)."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    try:
        config_yaml = yaml.dump(config, default_flow_style=False)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")
    
    business_repo.update_config_yaml(business_id, config_yaml)
    
    services = config.get('services', [])
    service_repo.sync_from_config(business_id, services)
    invalidate_agent_cache(business_id)
    
    return {"message": "Configuration updated", "config": config}


@router.put("/{business_id}/config/yaml", response_model=dict)
async def update_business_config_yaml(business_id: str, yaml_content: str = Body(...)):
    """Update business configuration from raw YAML string."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    try:
        config = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    
    business_repo.update_config_yaml(business_id, yaml_content)
    
    services = config.get('services', []) if config else []
    service_repo.sync_from_config(business_id, services)
    invalidate_agent_cache(business_id)
    
    return {"message": "Configuration updated"}


@router.get("/{business_id}/features", response_model=dict)
async def get_features(business_id: str):
    """Get enabled features for a business."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    features = business_repo.get_features(business_id)
    return {"features": features}


@router.put("/{business_id}/features", response_model=dict)
async def update_features(business_id: str, features: dict = Body(...)):
    """Update enabled features for a business."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    business_repo.update_features(business_id, features)
    return {"message": "Features updated", "features": features}


@router.get("/{business_id}/embed-code", response_model=dict)
async def get_embed_code(
    business_id: str,
    base_url: Optional[str] = Query(default="https://receptionist-ai.pragnyalabs.com/static"),
    api_url: Optional[str] = Query(default="https://receptionist-ai.pragnyalabs.com/api")
):
    """Get the embed code for the chat widget."""
    business = business_repo.find_by_id(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    embed_code = f'''<script src="{base_url}/chat.js" data-business-id="{business_id}" data-api-url="{api_url}"></script>'''
    
    return {
        "business_id": business_id,
        "business_name": business.name,
        "embed_code": embed_code,
        "instructions": "Add this script tag to your website's HTML, preferably before the closing </body> tag."
    }
