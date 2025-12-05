"""Chat API endpoints for the widget."""
import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import yaml

from app.db.database import get_db_connection
from app.models.conversation import ChatRequest, ChatResponse, ChatMessage, CustomerInfo
from app.agent.receptionist import create_receptionist_agent, load_business_config
from app.agent.prompts import get_greeting_message

router = APIRouter(prefix="/chat", tags=["Chat"])

agent_cache: dict = {}


def get_or_create_agent(business_id: str):
    """Get cached agent or create a new one."""
    if business_id in agent_cache:
        return agent_cache[business_id]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, type, config_yaml FROM businesses WHERE id = ?",
            (business_id,)
        )
        biz = cursor.fetchone()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Business not found")
        
        config = load_business_config(biz["config_yaml"])
        agent, toolkit = create_receptionist_agent(
            business_config=config,
            business_name=biz["name"],
            business_type=biz["type"]
        )
        
        agent_cache[business_id] = {
            "agent": agent,
            "toolkit": toolkit,
            "name": biz["name"],
            "type": biz["type"],
            "config": config
        }
        
        return agent_cache[business_id]


def get_or_create_conversation(business_id: str, session_id: str) -> dict:
    """Get or create a conversation session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE business_id = ? AND session_id = ?",
            (business_id, session_id)
        )
        conv = cursor.fetchone()
        
        if conv:
            return {
                "id": conv["id"],
                "messages": json.loads(conv["messages"] or "[]"),
                "customer_info": json.loads(conv["customer_info"] or "{}")
            }
        
        conv_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO conversations (id, business_id, session_id, messages, customer_info)
            VALUES (?, ?, ?, ?, ?)
        """, (conv_id, business_id, session_id, "[]", "{}"))
        conn.commit()
        
        return {
            "id": conv_id,
            "messages": [],
            "customer_info": {}
        }


def save_conversation(conv_id: str, messages: list, customer_info: dict):
    """Save conversation state."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE conversations 
            SET messages = ?, customer_info = ?, updated_at = ?
            WHERE id = ?
        """, (
            json.dumps(messages),
            json.dumps(customer_info),
            datetime.now().isoformat(),
            conv_id
        ))
        conn.commit()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI receptionist and get a response.
    """
    agent_data = get_or_create_agent(request.business_id)
    agent = agent_data["agent"]
    toolkit = agent_data["toolkit"]
    
    conversation = get_or_create_conversation(request.business_id, request.session_id)
    
    if request.customer_info:
        for field, value in request.customer_info.model_dump().items():
            if value:
                toolkit.customer_info[field] = value
                conversation["customer_info"][field] = value
    
    conversation["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    history = []
    for msg in conversation["messages"][:-1]:
        history.append({"role": msg["role"], "content": msg["content"]})
    
    try:
        response = agent.run(request.message, messages=history if history else None)
        assistant_message = response.content
    except Exception as e:
        assistant_message = "I apologize, but I'm having trouble processing your request right now. Please try again or contact us directly."
    
    conversation["messages"].append({
        "role": "assistant",
        "content": assistant_message,
        "timestamp": datetime.now().isoformat()
    })
    
    save_conversation(
        conversation["id"],
        conversation["messages"],
        toolkit.customer_info
    )
    
    customer_info_needed = []
    if toolkit.collecting_field:
        customer_info_needed.append(toolkit.collecting_field)
    
    return ChatResponse(
        session_id=request.session_id,
        message=assistant_message,
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
    
    conversation = get_or_create_conversation(business_id, actual_session_id)
    conversation["messages"].append({
        "role": "assistant",
        "content": greeting,
        "timestamp": datetime.now().isoformat()
    })
    save_conversation(conversation["id"], conversation["messages"], conversation["customer_info"])
    
    return {
        "session_id": actual_session_id,
        "message": greeting,
        "business_name": agent_data["name"]
    }


@router.get("/history/{business_id}/{session_id}")
async def get_chat_history(business_id: str, session_id: str):
    """Get chat history for a session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT messages, customer_info FROM conversations WHERE business_id = ? AND session_id = ?",
            (business_id, session_id)
        )
        conv = cursor.fetchone()
        
        if not conv:
            return {"messages": [], "customer_info": {}}
        
        return {
            "messages": json.loads(conv["messages"] or "[]"),
            "customer_info": json.loads(conv["customer_info"] or "{}")
        }


@router.delete("/session/{business_id}/{session_id}")
async def clear_session(business_id: str, session_id: str):
    """Clear a chat session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM conversations WHERE business_id = ? AND session_id = ?",
            (business_id, session_id)
        )
        conn.commit()
        
        return {"message": "Session cleared"}
