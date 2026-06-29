"""Enterprise tool definitions and execution for LLM tool-calling."""

import json
import logging
from typing import Any

from app.services import action_service

logger = logging.getLogger(__name__)

TOOL_TO_ACTION = {
    "get_profile": "get_profile",
    "create_support_ticket": "create_ticket",
    "generate_report": "generate_report",
    "lookup_employee": "fetch_employee",
    "lookup_customer": "fetch_customer",
    "query_enterprise_data": "query_data",
    "trigger_workflow": "trigger_workflow",
}

OPENAI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_profile",
            "description": (
                "Get the signed-in user's own profile: name, email, role, and linked employee record. "
                "Use ONLY when they ask about themselves — e.g. 'what is my name', 'my profile', "
                "'who am I', 'my email', 'my account details'."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": (
                "Create an IT or HR support ticket for a reported issue. "
                "Use when the user explicitly wants a ticket created for a problem."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string", "description": "Description of the issue"},
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                        "description": "Ticket priority",
                    },
                },
                "required": ["issue"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": (
                "Generate an enterprise report (HR headcount, sales, IT incidents, leave utilization). "
                "Use when the user asks to generate or create a report."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["hr", "sales", "it", "leave"],
                        "description": "Type of report to generate",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_employee",
            "description": (
                "Look up another employee's directory record by name or employee ID. "
                "Use when asking about a specific colleague, NOT for the signed-in user (use get_profile for that)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Employee name or ID such as EMP-1001",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": (
                "Look up a customer or client account by company name or customer ID. "
                "Use when the user asks about a specific customer account."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Customer name or ID such as CUST-5001",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_enterprise_data",
            "description": (
                "Run a query against company database tables (employees, customers, tickets, leave, policies). "
                "Use when the user wants to query or search enterprise records."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["database", "file"],
                        "description": "Whether to query a database table or file",
                    },
                    "source_name": {
                        "type": "string",
                        "description": "Table or file name, e.g. employees, tickets, employees.csv",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_workflow",
            "description": (
                "Trigger an enterprise workflow such as onboarding, offboarding, "
                "access provisioning, leave approval, or incident escalation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_key": {
                        "type": "string",
                        "enum": [
                            "onboarding",
                            "offboarding",
                            "access_provisioning",
                            "leave_approval",
                            "incident_escalation",
                        ],
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context for the workflow",
                    },
                },
                "required": [],
            },
        },
    },
]


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    user: Any,
    fallback_question: str,
) -> dict[str, Any]:
    """Execute a tool call and return a normalized action result."""
    logger.info("Executing tool=%s args=%s", tool_name, arguments)

    if tool_name == "get_profile":
        return action_service.get_profile(user)

    if tool_name == "create_support_ticket":
        issue = arguments.get("issue") or fallback_question
        priority = arguments.get("priority", "Medium")
        return action_service.create_ticket(issue=issue, user_id=user.id, priority=priority)

    if tool_name == "generate_report":
        report_type = arguments.get("report_type", "hr")
        return action_service.generate_report(report_type=report_type)

    if tool_name == "lookup_employee":
        query = arguments.get("query") or fallback_question
        employee_id = arguments.get("employee_id")
        return action_service.fetch_employee(query=query, employee_id=employee_id, user=user)

    if tool_name == "lookup_customer":
        query = arguments.get("query") or fallback_question
        customer_id = arguments.get("customer_id")
        return action_service.fetch_customer(query=query, customer_id=customer_id)

    if tool_name == "query_enterprise_data":
        source_type = arguments.get("source_type")
        source_name = arguments.get("source_name")
        if source_type and source_name:
            return action_service.query_data(
                source_type=source_type,
                source_name=source_name,
                user=user,
            )
        return action_service.query_data(question=fallback_question, user=user)

    if tool_name == "trigger_workflow":
        return action_service.trigger_workflow(
            workflow_key=arguments.get("workflow_key"),
            context=arguments.get("context"),
            question=fallback_question,
        )

    raise ValueError(f"Unknown tool: {tool_name}")


def parse_openai_tool_arguments(raw: str | None) -> dict[str, Any]:
    """Parse JSON arguments from an OpenAI tool call."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
