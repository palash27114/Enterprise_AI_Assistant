"""Enterprise action handlers backed by PostgreSQL."""

import logging
import re
import uuid
from typing import Any

from app.services import (
    customer_service,
    employee_service,
    query_service,
    report_service,
    ticket_service,
    workflow_service,
)

logger = logging.getLogger(__name__)

ActionResult = dict[str, Any]


def execute(action: str, question: str, user_id: str | None = None, user: Any | None = None) -> ActionResult:
    """Run a business action from natural language (used by POST /ask)."""
    if action == "get_profile":
        if user is None:
            raise ValueError("User is required for profile lookup.")
        return get_profile(user)

    handlers = {
        "create_ticket": lambda: create_ticket(issue=question, user_id=user_id),
        "generate_report": lambda: generate_report(report_type=_detect_report_type(question)),
        "fetch_employee": lambda: fetch_employee(query=question, user=user),
        "fetch_customer": lambda: fetch_customer(query=question),
        "query_data": lambda: query_data(question=question, user=user),
        "trigger_workflow": lambda: trigger_workflow(question=question),
    }

    handler = handlers.get(action)
    if not handler:
        raise ValueError(f"Unsupported action: {action}")

    result = handler()
    logger.info("Executed action=%s", action)
    return result


def create_ticket(issue: str, user_id: str | None = None, priority: str = "Medium") -> ActionResult:
    """Create a support ticket."""
    ticket = ticket_service.create_ticket(issue, user_id=user_id, priority=priority)
    return {
        "response": f"Support ticket {ticket['id']} created successfully.",
        "action": "create_ticket",
        "ticket_id": ticket["id"],
        "status": ticket["status"],
        "data": ticket,
    }


def generate_report(report_type: str = "hr", period: str = "current_quarter") -> ActionResult:
    """Generate an enterprise report from live database metrics."""
    data = report_service.generate_report(report_type=report_type, period=period)
    metrics = data["metrics"]
    metric_lines = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in metrics.items())
    response = f"Generated {data['title']} ({data['report_id']}). Summary — {metric_lines}."

    return {
        "response": response,
        "action": "generate_report",
        "ticket_id": None,
        "status": "Completed",
        "data": data,
    }


def list_employees(user: Any, search: str | None = None) -> list[dict[str, Any]]:
    """Return employees visible to the signed-in user."""
    return employee_service.list_visible_employees(user, search=search)


def get_employee(employee_id: str, user: Any | None = None) -> dict[str, Any] | None:
    """Return one employee by ID if visible to the user."""
    record = employee_service.get_employee_record(employee_id)
    if not record:
        return None
    if user is not None and not employee_service.can_view_employee(user, employee_id):
        return None
    return record


def fetch_employee(query: str | None = None, employee_id: str | None = None, user: Any | None = None) -> ActionResult:
    """Look up an employee by ID or search query."""
    employee = get_employee(employee_id, user=user) if employee_id else _find_employee(query or "", user=user)
    if not employee:
        return {
            "response": "No matching employee found in your visible directory.",
            "action": "fetch_employee",
            "ticket_id": None,
            "status": "Not Found",
            "data": {"matches": []},
        }

    response = (
        f"Found employee {employee['name']} ({employee['employee_id']}) — "
        f"{employee['role']} in {employee['department']}, {employee['location']}."
    )
    return {
        "response": response,
        "action": "fetch_employee",
        "ticket_id": None,
        "status": "Found",
        "data": {"employee": employee},
    }


def list_customers(search: str | None = None) -> list[dict[str, Any]]:
    """Return customer accounts from the database."""
    return customer_service.list_customers(search=search)


def get_customer(customer_id: str) -> dict[str, Any] | None:
    """Return one customer by ID."""
    return customer_service.get_customer_record(customer_id)


def fetch_customer(query: str | None = None, customer_id: str | None = None) -> ActionResult:
    """Look up a customer by ID or search query."""
    customer = get_customer(customer_id) if customer_id else _find_customer(query or "")
    if not customer:
        return {
            "response": "No matching customer found. Try Acme Corporation or customer ID CUST-5001.",
            "action": "fetch_customer",
            "ticket_id": None,
            "status": "Not Found",
            "data": {"matches": []},
        }

    response = (
        f"Found customer {customer['name']} ({customer['customer_id']}) — "
        f"{customer['segment']} account, MRR ${customer['mrr_usd']:,}, status {customer['status']}."
    )
    return {
        "response": response,
        "action": "fetch_customer",
        "ticket_id": None,
        "status": "Found",
        "data": {"customer": customer},
    }


def query_data(
    source_type: str | None = None,
    source_name: str | None = None,
    question: str | None = None,
    limit: int = 10,
    user: Any | None = None,
) -> ActionResult:
    """Query enterprise data stored in PostgreSQL."""
    result = query_service.run_query(
        user=user,
        source_type=source_type,
        source_name=source_name,
        question=question,
        limit=limit,
    )
    query_id = f"QRY-{uuid.uuid4().hex[:8].upper()}"
    data = {"query_id": query_id, **result}

    response = (
        f"Query {query_id} executed against {result['source_type']} `{result['source_name']}`. "
        f"Returned {result['row_count']} record(s)."
    )
    return {
        "response": response,
        "action": "query_data",
        "ticket_id": None,
        "status": "Success",
        "data": data,
    }


def list_workflows() -> list[dict[str, Any]]:
    """Return available workflow definitions."""
    return workflow_service.list_workflow_definitions()


def trigger_workflow(workflow_key: str | None = None, question: str | None = None, context: str | None = None) -> ActionResult:
    """Trigger a workflow and persist the execution."""
    resolved_key = workflow_key or _detect_workflow(question or "")
    definition = workflow_service.get_workflow_definition(resolved_key)
    if not definition:
        resolved_key = "onboarding"
        definition = workflow_service.get_workflow_definition(resolved_key)

    if not definition:
        return {
            "response": "No workflows are configured.",
            "action": "trigger_workflow",
            "ticket_id": None,
            "status": "Failed",
            "data": {},
        }

    data = workflow_service.trigger_workflow(resolved_key, context=context)
    response = (
        f"Workflow {data['name']} triggered ({data['workflow_id']}). "
        f"Status: Queued — {len(data['steps'])} steps scheduled."
    )
    return {
        "response": response,
        "action": "trigger_workflow",
        "ticket_id": None,
        "status": "Triggered",
        "data": data,
    }


def get_profile(user: Any) -> ActionResult:
    """Return the authenticated user's profile with a linked employee record."""
    employee = employee_service.get_employee_for_user(user)
    access_role = employee["access_role"] if employee else None
    data = {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "provider": user.provider,
        "workspace_role": employee_service.get_access_role_label(access_role or ""),
        "job_title": employee["job_title"] if employee else None,
        "access_role": access_role,
        "employee": employee,
    }

    if employee:
        response = (
            f"Your name is {user.full_name}. "
            f"You are a {employee['job_title']} in the {employee['department']} department "
            f"({employee['employee_id']}, {employee['location']}). "
            f"Email: {user.email}."
        )
        status = "Found"
    else:
        response = f"Your name is {user.full_name}. Email: {user.email}."
        status = "Partial"

    return {
        "response": response,
        "action": "get_profile",
        "ticket_id": None,
        "status": status,
        "data": data,
    }


def _find_employee(query: str, user: Any | None = None) -> dict[str, Any] | None:
    lowered = query.lower()
    visible = employee_service.list_visible_employees(user) if user else employee_service.list_all_employees()

    id_match = re.search(r"\bemp-\d+\b", lowered)
    if id_match:
        employee_id = id_match.group(0).upper()
        return next((e for e in visible if e["employee_id"].upper() == employee_id), None)

    for employee in visible:
        if employee["name"].lower() in lowered:
            return employee

    for employee in visible:
        token = employee["name"].split()[0].lower()
        if token in lowered.split():
            return employee

    return None


def _detect_report_type(question: str) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ("sales", "revenue", "mrr", "deal")):
        return "sales"
    if any(word in lowered for word in ("it", "incident", "ticket", "support")):
        return "it"
    if any(word in lowered for word in ("leave", "pto", "vacation", "absence")):
        return "leave"
    return "hr"


def _detect_workflow(question: str) -> str:
    lowered = question.lower()
    if "offboard" in lowered:
        return "offboarding"
    if any(word in lowered for word in ("access", "provision", "vpn", "login")):
        return "access_provisioning"
    if any(word in lowered for word in ("leave", "pto", "vacation", "approval")):
        return "leave_approval"
    if any(word in lowered for word in ("incident", "escalat", "outage", "ticket")):
        return "incident_escalation"
    return "onboarding"


def _find_customer(question: str) -> dict[str, Any] | None:
    lowered = question.lower()

    id_match = re.search(r"\bcust-\d+\b", lowered)
    if id_match:
        return get_customer(id_match.group(0))

    customers = customer_service.list_customers()
    for customer in customers:
        if customer["name"].lower() in lowered:
            return customer

    for customer in customers:
        token = customer["name"].split()[0].lower()
        if token in lowered.split():
            return customer

    return None
