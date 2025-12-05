"""Workflow execution tools for V3 custom workflow builder."""
from typing import Optional
import re

from app.repositories import workflow_repo, lead_repo


def check_workflow_triggers(
    business_id: str,
    message: str,
    customer_data: Optional[dict] = None
) -> list[dict]:
    """
    Check if any workflows should be triggered based on message and customer data.
    
    Args:
        business_id: Business ID
        message: Customer's message
        customer_data: Customer context (is_returning, visit_count, etc.)
    
    Returns:
        List of workflows that should be triggered
    """
    workflows = workflow_repo.find_active_by_business(business_id)
    triggered = []
    
    message_lower = message.lower()
    customer_data = customer_data or {}
    
    for workflow in workflows:
        should_trigger = False
        
        if workflow.trigger_type == "keyword":
            keywords = workflow.trigger_config.keywords or []
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    should_trigger = True
                    break
        
        elif workflow.trigger_type == "segment":
            customer_type = workflow.trigger_config.customer_type
            min_visits = workflow.trigger_config.segment
            
            if customer_type == "new" and not customer_data.get("is_returning"):
                should_trigger = True
            elif customer_type == "returning" and customer_data.get("is_returning"):
                if min_visits:
                    try:
                        if customer_data.get("visit_count", 0) >= int(min_visits):
                            should_trigger = True
                    except:
                        should_trigger = True
                else:
                    should_trigger = True
        
        elif workflow.trigger_type == "time":
            time_condition = workflow.trigger_config.time_condition
            if time_condition == "first_message" and customer_data.get("is_first_message"):
                should_trigger = True
        
        if should_trigger:
            triggered.append({
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "trigger_type": workflow.trigger_type,
                "actions": [{"type": a.type, "config": a.config} for a in workflow.actions]
            })
    
    return triggered


def execute_workflow(
    business_id: str,
    workflow_id: str,
    context: dict
) -> dict:
    """
    Execute a workflow's actions.
    
    Args:
        business_id: Business ID
        workflow_id: Workflow to execute
        context: Execution context including customer info, conversation state
    
    Returns:
        {
            "actions_taken": ["action1", "action2"],
            "result": "Description of what happened",
            "messages": ["Message to send to customer"],
            "discounts": [{"percent": 20, "reason": "birthday"}]
        }
    """
    workflow = workflow_repo.find_by_id_and_business(workflow_id, business_id)
    if not workflow:
        return {
            "actions_taken": [],
            "result": "Workflow not found",
            "messages": [],
            "discounts": []
        }
    
    actions_taken = []
    messages = []
    discounts = []
    lead_captured = None
    
    for action in workflow.actions:
        action_type = action.type
        action_config = action.config
        
        if action_type == "send_message":
            message = action_config.get("message", "")
            message = _interpolate_message(message, context)
            messages.append(message)
            actions_taken.append("sent_message")
        
        elif action_type == "apply_discount":
            percent = action_config.get("percent", 0)
            reason = action_config.get("reason", "promotion")
            discounts.append({
                "percent": percent,
                "reason": reason,
                "code": _generate_discount_code(percent, reason)
            })
            actions_taken.append(f"applied_{percent}%_discount")
        
        elif action_type == "capture_lead":
            interest = action_config.get("interest", workflow.name)
            customer_info = context.get("customer_info", {})
            
            if customer_info.get("first_name") or customer_info.get("phone") or customer_info.get("email"):
                name = f"{customer_info.get('first_name', '')} {customer_info.get('last_name', '')}".strip()
                lead_id, _ = lead_repo.create_or_update(
                    business_id=business_id,
                    name=name or "Unknown",
                    interest=interest,
                    email=customer_info.get("email"),
                    phone=customer_info.get("phone"),
                    notes=f"Captured via workflow: {workflow.name}",
                    source="workflow"
                )
                lead_captured = lead_id
                actions_taken.append("captured_lead")
            else:
                actions_taken.append("lead_capture_pending")
        
        elif action_type == "offer_service":
            service_type = action_config.get("service_type", "")
            messages.append(f"I'd be happy to tell you more about our {service_type} options!")
            actions_taken.append(f"offered_{service_type}")
        
        elif action_type == "escalate":
            messages.append("Let me connect you with a team member who can better assist you.")
            actions_taken.append("escalated")
    
    result_parts = []
    if discounts:
        result_parts.append(f"Applied {discounts[0]['percent']}% {discounts[0]['reason']} discount")
    if lead_captured:
        result_parts.append("Captured lead information")
    if messages:
        result_parts.append(f"Sent {len(messages)} message(s)")
    
    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.name,
        "actions_taken": actions_taken,
        "result": "; ".join(result_parts) if result_parts else "Workflow executed",
        "messages": messages,
        "discounts": discounts,
        "lead_id": lead_captured
    }


def execute_triggered_workflows(
    business_id: str,
    message: str,
    customer_data: Optional[dict] = None,
    context: Optional[dict] = None
) -> dict:
    """
    Check for triggers and execute any matching workflows.
    
    Args:
        business_id: Business ID
        message: Customer's message
        customer_data: Customer info
        context: Additional execution context
    
    Returns:
        Combined results from all triggered workflows
    """
    triggered = check_workflow_triggers(business_id, message, customer_data)
    
    if not triggered:
        return {
            "triggered": False,
            "workflows_executed": [],
            "messages": [],
            "discounts": []
        }
    
    all_messages = []
    all_discounts = []
    workflows_executed = []
    
    exec_context = context or {}
    exec_context["customer_info"] = customer_data or {}
    exec_context["message"] = message
    
    for workflow_info in triggered:
        result = execute_workflow(business_id, workflow_info["workflow_id"], exec_context)
        
        workflows_executed.append({
            "workflow_id": workflow_info["workflow_id"],
            "workflow_name": workflow_info["workflow_name"],
            "actions_taken": result["actions_taken"],
            "result": result["result"]
        })
        
        all_messages.extend(result.get("messages", []))
        all_discounts.extend(result.get("discounts", []))
    
    return {
        "triggered": True,
        "workflows_executed": workflows_executed,
        "messages": all_messages,
        "discounts": all_discounts
    }


def _interpolate_message(message: str, context: dict) -> str:
    """Replace placeholders in message with context values."""
    customer_info = context.get("customer_info", {})
    
    replacements = {
        "{name}": customer_info.get("first_name", "there"),
        "{first_name}": customer_info.get("first_name", "there"),
        "{visit_count}": str(customer_info.get("visit_count", 0)),
    }
    
    for placeholder, value in replacements.items():
        message = message.replace(placeholder, value)
    
    return message


def _generate_discount_code(percent: int, reason: str) -> str:
    """Generate a discount code."""
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    reason_prefix = reason.upper()[:4] if reason else "DISC"
    return f"{reason_prefix}{percent}{suffix}"
