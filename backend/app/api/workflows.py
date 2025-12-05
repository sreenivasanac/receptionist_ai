"""Workflows API endpoints for V3 custom workflow builder."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.repositories.workflows import (
    workflow_repo,
    WorkflowCreate,
    WorkflowUpdate,
    Workflow
)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/{business_id}")
async def list_workflows(
    business_id: str,
    active_only: bool = Query(default=False)
):
    """List all workflows for a business."""
    if active_only:
        workflows = workflow_repo.find_active_by_business(business_id)
    else:
        workflows = workflow_repo.find_all_by_business(business_id)
    
    return {
        "workflows": [w.model_dump() if hasattr(w, 'model_dump') else w for w in workflows],
        "count": len(workflows)
    }


@router.post("/{business_id}")
async def create_workflow(
    business_id: str,
    data: WorkflowCreate
):
    """Create a new workflow."""
    workflow_id = workflow_repo.create(business_id, data)
    workflow = workflow_repo.find_by_id(workflow_id)
    
    return {
        "message": "Workflow created successfully",
        "workflow": workflow.model_dump() if workflow else {"id": workflow_id}
    }


@router.get("/{business_id}/templates")
async def get_templates(business_id: str):
    """Get pre-built workflow templates."""
    templates = workflow_repo.get_templates()
    return {
        "templates": templates,
        "count": len(templates)
    }


@router.post("/{business_id}/from-template")
async def create_from_template(
    business_id: str,
    template_name: str = Query(..., description="Name of the template to use")
):
    """Create a workflow from a pre-built template."""
    workflow_id = workflow_repo.create_from_template(business_id, template_name)
    
    if not workflow_id:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    workflow = workflow_repo.find_by_id(workflow_id)
    
    return {
        "message": f"Workflow created from template '{template_name}'",
        "workflow": workflow.model_dump() if workflow else {"id": workflow_id}
    }


@router.get("/{business_id}/{workflow_id}")
async def get_workflow(
    business_id: str,
    workflow_id: str
):
    """Get a specific workflow."""
    workflow = workflow_repo.find_by_id_and_business(workflow_id, business_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"workflow": workflow.model_dump()}


@router.put("/{business_id}/{workflow_id}")
async def update_workflow(
    business_id: str,
    workflow_id: str,
    data: WorkflowUpdate
):
    """Update a workflow."""
    success = workflow_repo.update(business_id, workflow_id, data)
    
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflow_repo.find_by_id_and_business(workflow_id, business_id)
    
    return {
        "message": "Workflow updated successfully",
        "workflow": workflow.model_dump() if workflow else None
    }


@router.delete("/{business_id}/{workflow_id}")
async def delete_workflow(
    business_id: str,
    workflow_id: str
):
    """Delete a workflow."""
    success = workflow_repo.delete_by_id_and_business(workflow_id, business_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"message": "Workflow deleted successfully"}


@router.post("/{business_id}/{workflow_id}/toggle")
async def toggle_workflow(
    business_id: str,
    workflow_id: str
):
    """Toggle workflow active status."""
    new_status = workflow_repo.toggle_active(business_id, workflow_id)
    
    if new_status is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {
        "message": f"Workflow {'activated' if new_status else 'deactivated'}",
        "is_active": new_status
    }


@router.get("/{business_id}/by-trigger/{trigger_type}")
async def get_by_trigger_type(
    business_id: str,
    trigger_type: str
):
    """Get active workflows by trigger type."""
    valid_types = ["keyword", "segment", "time"]
    if trigger_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger type. Must be one of: {valid_types}"
        )
    
    workflows = workflow_repo.find_by_trigger_type(business_id, trigger_type)
    
    return {
        "trigger_type": trigger_type,
        "workflows": [w.model_dump() for w in workflows],
        "count": len(workflows)
    }
