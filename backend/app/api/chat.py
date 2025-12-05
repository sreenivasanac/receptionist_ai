"""Chat API endpoints for the widget."""
import uuid
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.repositories import business_repo, conversation_repo
from app.models.conversation import ChatRequest, ChatResponse, InputConfig, ServiceOption, TimeSlotOption
from app.agent.receptionist import create_receptionist_agent, load_business_config
from app.agent.prompts import get_greeting_message

router = APIRouter(prefix="/chat", tags=["Chat"])

agent_cache: dict = {}


def invalidate_agent_cache(business_id: str):
    """Remove a business from the agent cache to force reload on next request."""
    if business_id in agent_cache:
        del agent_cache[business_id]


def get_or_create_agent(business_id: str, force_refresh: bool = False):
    """Get cached agent or create a new one."""
    if business_id in agent_cache and not force_refresh:
        return agent_cache[business_id]
    
    biz_info = business_repo.get_basic_info(business_id)
    if not biz_info:
        raise HTTPException(status_code=404, detail="Business not found")
    
    config = load_business_config(biz_info["config_yaml"])
    agent, toolkit = create_receptionist_agent(
        business_config=config,
        business_name=biz_info["name"],
        business_type=biz_info["type"],
        business_id=business_id
    )
    
    agent_cache[business_id] = {
        "agent": agent,
        "toolkit": toolkit,
        "name": biz_info["name"],
        "type": biz_info["type"],
        "config": config
    }
    
    return agent_cache[business_id]


def extract_slot_id(message: str) -> tuple[str, str | None]:
    """Extract slot_id from message if present. Returns (clean_message, slot_id)."""
    match = re.search(r'\[slot:([^\]]+)\]', message)
    if match:
        slot_id = match.group(1)
        clean_message = re.sub(r'\s*\[slot:[^\]]+\]', '', message)
        return clean_message, slot_id
    return message, None


def extract_service_id(message: str) -> tuple[str, str | None]:
    """Extract service_id from message if present. Returns (clean_message, service_id)."""
    match = re.search(r'\[service_id:([^\]]+)\]', message)
    if match:
        service_id = match.group(1)
        clean_message = re.sub(r'\s*\[service_id:[^\]]+\]', '', message)
        return clean_message, service_id
    return message, None


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the AI receptionist and get a response."""
    agent_data = get_or_create_agent(request.business_id)
    agent = agent_data["agent"]
    toolkit = agent_data["toolkit"]
    
    conversation = conversation_repo.get_or_create(request.business_id, request.session_id)
    
    if request.customer_info:
        for field, value in request.customer_info.model_dump().items():
            if value:
                toolkit.customer_info[field] = value
                conversation["customer_info"][field] = value
    
    # Extract slot_id if present
    message_text, slot_id = extract_slot_id(request.message)
    if slot_id:
        toolkit.selected_slot_id = slot_id
    
    # Extract service_id if present (from structured service selection)
    message_text, service_id = extract_service_id(message_text)
    if service_id:
        toolkit.selected_service_id = service_id
        # Clear any pending service_select UI since service is now selected
        if toolkit.pending_input_type == "service_select":
            toolkit.pending_input_type = None
            toolkit.pending_input_config = None
    
    conversation["messages"].append({
        "role": "user",
        "content": message_text,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        response = agent.run(message_text, session_id=request.session_id)
        assistant_message = response.content
    except Exception as e:
        assistant_message = "I apologize, but I'm having trouble processing your request right now. Please try again or contact us directly."
    
    conversation["messages"].append({
        "role": "assistant",
        "content": assistant_message,
        "timestamp": datetime.now().isoformat()
    })
    
    conversation_repo.save(
        conversation["id"],
        conversation["messages"],
        toolkit.customer_info
    )
    
    customer_info_needed = []
    if toolkit.collecting_field:
        customer_info_needed.append(toolkit.collecting_field)
    
    input_type = toolkit.pending_input_type or "text"
    input_config = None
    
    if toolkit.pending_input_config:
        config_data = toolkit.pending_input_config
        
        if input_type == "service_select" and config_data.get("services"):
            services = [
                ServiceOption(
                    id=s.get("id", s.get("name", "").lower().replace(" ", "_")),
                    name=s.get("name", ""),
                    price=float(s.get("price", 0)),
                    duration_minutes=s.get("duration_minutes"),
                    description=s.get("description")
                )
                for s in config_data.get("services", [])
            ]
            input_config = InputConfig(
                services=services,
                multi_select=config_data.get("multi_select", False)
            )
        elif input_type == "contact_form":
            input_config = InputConfig(
                fields=config_data.get("fields", ["name", "phone"])
            )
        elif input_type == "datetime_picker":
            slots = None
            if config_data.get("slots"):
                slots = [
                    TimeSlotOption(
                        id=s.get("id", ""),
                        date=s.get("date", ""),
                        time=s.get("time", ""),
                        staff_id=s.get("staff_id"),
                        staff_name=s.get("staff_name"),
                        duration_minutes=s.get("duration_minutes")
                    )
                    for s in config_data.get("slots", [])
                ]
            input_config = InputConfig(
                min_date=config_data.get("min_date"),
                max_date=config_data.get("max_date"),
                available_dates=config_data.get("available_dates"),
                time_slots=config_data.get("time_slots"),
                slots=slots
            )
        
        toolkit.pending_input_type = None
        toolkit.pending_input_config = None
    
    return ChatResponse(
        session_id=request.session_id,
        message=assistant_message,
        input_type=input_type,
        input_config=input_config,
        customer_info_needed=customer_info_needed,
        actions=[]
    )


@router.get("/greeting/{business_id}")
async def get_greeting(business_id: str, session_id: Optional[str] = None):
    """Get the initial greeting message for a business."""
    agent_data = get_or_create_agent(business_id)
    
    greeting = get_greeting_message(
        agent_data["name"],
        agent_data["type"]
    )
    
    actual_session_id = session_id or str(uuid.uuid4())
    
    conversation = conversation_repo.get_or_create(business_id, actual_session_id)
    conversation["messages"].append({
        "role": "assistant",
        "content": greeting,
        "timestamp": datetime.now().isoformat()
    })
    conversation_repo.save(conversation["id"], conversation["messages"], conversation["customer_info"])
    
    return {
        "session_id": actual_session_id,
        "message": greeting,
        "business_name": agent_data["name"]
    }


@router.get("/history/{business_id}/{session_id}")
async def get_chat_history(business_id: str, session_id: str):
    """Get chat history for a session."""
    return conversation_repo.get_history(business_id, session_id)


@router.delete("/session/{business_id}/{session_id}")
async def clear_session(business_id: str, session_id: str):
    """Clear a chat session."""
    conversation_repo.delete_by_session(business_id, session_id)
    return {"message": "Session cleared"}


@router.post("/admin/refresh-agent/{business_id}")
async def refresh_agent(business_id: str):
    """Force refresh an agent to pick up new prompts/config."""
    invalidate_agent_cache(business_id)
    get_or_create_agent(business_id, force_refresh=True)
    return {"message": f"Agent refreshed for business {business_id}"}


@router.post("/admin/refresh-all-agents")
async def refresh_all_agents():
    """Force refresh all cached agents."""
    cleared = list(agent_cache.keys())
    agent_cache.clear()
    return {"message": f"Cleared {len(cleared)} cached agents", "cleared": cleared}
