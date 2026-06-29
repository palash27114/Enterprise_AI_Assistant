"""Simulated enterprise action handlers backed by mock data."""

import logging
import re
import uuid
from typing import Any

from app.data import mock_data
from app.services import ticket_service

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
        "fetch_employee": lambda: fetch_employee(query=question),
        "fetch_customer": lambda: fetch_customer(query=question),
        "query_data": lambda: query_data(question=question),
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
    ticket = ticket_service.create_ticket(issue, user_id=user_id)
    ticket["priority"] = priority
    return {
        "response": f"Support ticket {ticket['id']} created successfully.",
        "action": "create_ticket",
        "ticket_id": ticket["id"],
        "status": ticket["status"],
        "data": ticket,
    }


def generate_report(report_type: str = "hr", period: str = "current_quarter") -> ActionResult:
    """Generate a mock enterprise report."""
    if report_type not in mock_data.REPORT_TEMPLATES:
        report_type = "hr"

    template = mock_data.REPORT_TEMPLATES[report_type]
    report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    generated_at = mock_data.utc_now_iso()

    data = {
        "report_id": report_id,
        "title": template["title"],
        "type": report_type,
        "generated_at": generated_at,
        "metrics": template["metrics"],
        "format": "pdf",
        "download_url": f"/mock/reports/{report_id}.pdf",
        "period": period,
    }

    metrics = template["metrics"]
    metric_lines = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in metrics.items())
    response = f"Generated {template['title']} ({report_id}). Summary — {metric_lines}."

    return {
        "response": response,
        "action": "generate_report",
        "ticket_id": None,
        "status": "Completed",
        "data": data,
    }


def list_employees() -> list[dict[str, Any]]:
    """Return all mock employees."""
    return list(mock_data.EMPLOYEES)


def get_employee(employee_id: str) -> dict[str, Any] | None:
    """Return one employee by ID."""
    normalized = employee_id.upper()
    for employee in mock_data.EMPLOYEES:
        if employee["employee_id"].upper() == normalized:
            return employee
    return None


def fetch_employee(query: str | None = None, employee_id: str | None = None) -> ActionResult:
    """Look up an employee by ID or search query."""
    employee = get_employee(employee_id) if employee_id else _find_employee(query or "")
    if not employee:
        return {
            "response": "No matching employee found. Try Palash Joshi or employee ID EMP-1001.",
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


def list_customers() -> list[dict[str, Any]]:
    """Return all mock customers."""
    return list(mock_data.CUSTOMERS)


def get_customer(customer_id: str) -> dict[str, Any] | None:
    """Return one customer by ID."""
    normalized = customer_id.upper()
    for customer in mock_data.CUSTOMERS:
        if customer["customer_id"].upper() == normalized:
            return customer
    return None


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
) -> ActionResult:
    """Run a simulated database or file query."""
    if source_type and source_name:
        rows = _rows_for_source(source_type, source_name)
        resolved_type = source_type
        resolved_name = source_name
    else:
        resolved_type, resolved_name, rows = _resolve_query_target(question or "")

    query_id = f"QRY-{uuid.uuid4().hex[:8].upper()}"
    data = {
        "query_id": query_id,
        "source_type": resolved_type,
        "source_name": resolved_name,
        "row_count": len(rows),
        "rows": rows[:limit],
        "executed_at": mock_data.utc_now_iso(),
        "simulated": True,
    }

    response = (
        f"Query {query_id} executed against {resolved_type} `{resolved_name}`. "
        f"Returned {len(rows)} record(s)."
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
    return [
        {"workflow_key": key, "name": value["name"], "steps": value["steps"]}
        for key, value in mock_data.WORKFLOW_DEFINITIONS.items()
    ]


def trigger_workflow(workflow_key: str | None = None, question: str | None = None, context: str | None = None) -> ActionResult:
    """Trigger a simulated workflow."""
    resolved_key = workflow_key or _detect_workflow(question or "")
    if resolved_key not in mock_data.WORKFLOW_DEFINITIONS:
        resolved_key = "onboarding"

    workflow = mock_data.WORKFLOW_DEFINITIONS[resolved_key]
    workflow_id = f"WF-{uuid.uuid4().hex[:8].upper()}"

    data = {
        "workflow_id": workflow_id,
        "workflow_key": resolved_key,
        "name": workflow["name"],
        "status": "Triggered",
        "steps": workflow["steps"],
        "triggered_at": mock_data.utc_now_iso(),
        "simulated": True,
        "context": context,
    }

    response = (
        f"Workflow {workflow['name']} triggered ({workflow_id}). "
        f"Status: Queued — {len(workflow['steps'])} steps scheduled."
    )
    return {
        "response": response,
        "action": "trigger_workflow",
        "ticket_id": None,
        "status": "Triggered",
        "data": data,
    }


def get_profile(user: Any) -> ActionResult:
    """Return the authenticated user's profile with a linked mock employee record."""
    employee = _find_employee_by_user(user)
    data = {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "provider": user.provider,
        "workspace_role": "Workspace member",
        "employee": employee,
    }

    if employee:
        response = (
            f"Your name is {user.full_name}. "
            f"You are a {employee['role']} in the {employee['department']} department "
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


def _find_employee_by_user(user: Any) -> dict[str, Any] | None:
    email = user.email.lower()
    name = user.full_name.lower()
    for employee in mock_data.EMPLOYEES:
        if employee["email"].lower() == email or employee["name"].lower() == name:
            return employee
    for employee in mock_data.EMPLOYEES:
        if employee["name"].split()[0].lower() in name:
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


def _find_employee(question: str) -> dict[str, Any] | None:
    lowered = question.lower()

    id_match = re.search(r"\bemp-\d+\b", lowered)
    if id_match:
        return get_employee(id_match.group(0))

    for employee in mock_data.EMPLOYEES:
        if employee["name"].lower() in lowered:
            return employee

    for employee in mock_data.EMPLOYEES:
        first_name = employee["name"].split()[0].lower()
        if first_name in lowered.split():
            return employee

    return mock_data.EMPLOYEES[0] if question.strip() else None


def _find_customer(question: str) -> dict[str, Any] | None:
    lowered = question.lower()

    id_match = re.search(r"\bcust-\d+\b", lowered)
    if id_match:
        return get_customer(id_match.group(0))

    for customer in mock_data.CUSTOMERS:
        if customer["name"].lower() in lowered:
            return customer

    for customer in mock_data.CUSTOMERS:
        token = customer["name"].split()[0].lower()
        if token in lowered.split():
            return customer

    return mock_data.CUSTOMERS[0] if question.strip() else None


def _rows_for_source(source_type: str, source_name: str) -> list[dict[str, Any]]:
    if source_type == "file":
        return list(mock_data.FILE_SOURCES.get(source_name, []))
    return list(mock_data.DATABASE_TABLES.get(source_name, []))


def _resolve_query_target(question: str) -> tuple[str, str, list[dict[str, Any]]]:
    lowered = question.lower()

    for filename, rows in mock_data.FILE_SOURCES.items():
        if filename.replace(".csv", "") in lowered or filename in lowered:
            return "file", filename, rows

    if "leave" in lowered:
        return "database", "leave_requests", mock_data.DATABASE_TABLES["leave_requests"]
    if "ticket" in lowered or "incident" in lowered:
        return "database", "tickets", mock_data.DATABASE_TABLES["tickets"]
    if "customer" in lowered or "client" in lowered:
        return "database", "customers", mock_data.DATABASE_TABLES["customers"]
    if "employee" in lowered or "staff" in lowered:
        return "database", "employees", mock_data.DATABASE_TABLES["employees"]

    if "file" in lowered or "csv" in lowered:
        return "file", "employees.csv", mock_data.FILE_SOURCES["employees.csv"]

    return "database", "employees", mock_data.DATABASE_TABLES["employees"]
