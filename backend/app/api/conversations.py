"""Conversations API endpoints for V3 history viewing."""
import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, Query, Response

from app.repositories import conversation_repo

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/{business_id}")
async def list_conversations(
    business_id: str,
    query: Optional[str] = Query(default=None, description="Search in messages and customer info"),
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """List and search conversations."""
    conversations = conversation_repo.search(
        business_id=business_id,
        query=query,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    total = conversation_repo.count_search(
        business_id=business_id,
        query=query,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "conversations": conversations,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(conversations) < total
    }


@router.get("/{business_id}/{session_id}")
async def get_conversation(
    business_id: str,
    session_id: str
):
    """Get a specific conversation with full details."""
    conversation = conversation_repo.find_by_session(business_id, session_id)
    
    if not conversation:
        return {"error": "Conversation not found"}
    
    summary = conversation_repo.get_summary(business_id, session_id)
    
    return {
        "conversation": conversation,
        "summary": summary
    }


@router.get("/{business_id}/{session_id}/export")
async def export_conversation(
    business_id: str,
    session_id: str,
    format: str = Query(default="json", description="Export format: json or csv")
):
    """Export a single conversation."""
    data = conversation_repo.export(
        business_id=business_id,
        session_id=session_id,
        format=format
    )
    
    if not data:
        return {"error": "Conversation not found"}
    
    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=conversation_{session_id[:8]}.csv"}
        )
    else:
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=conversation_{session_id[:8]}.json"}
        )


@router.get("/{business_id}/export/all")
async def export_all_conversations(
    business_id: str,
    format: str = Query(default="json"),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None)
):
    """Export all conversations for a business."""
    data = conversation_repo.export(
        business_id=business_id,
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=conversations_export.csv"}
        )
    else:
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=conversations_export.json"}
        )


@router.get("/{business_id}/{session_id}/summary")
async def get_conversation_summary(
    business_id: str,
    session_id: str
):
    """Get a summary of a conversation."""
    summary = conversation_repo.get_summary(business_id, session_id)
    
    if not summary:
        return {"error": "Conversation not found"}
    
    return {"summary": summary}


@router.delete("/{business_id}/{session_id}")
async def delete_conversation(
    business_id: str,
    session_id: str
):
    """Delete a conversation."""
    success = conversation_repo.delete_by_session(business_id, session_id)
    
    if not success:
        return {"error": "Conversation not found or already deleted"}
    
    return {"message": "Conversation deleted successfully"}
