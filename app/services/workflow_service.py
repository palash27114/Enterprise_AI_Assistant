"""Workflow definitions and executions from PostgreSQL."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.models import WorkflowDefinition, WorkflowExecution
from app.db.session import get_session


def list_workflow_definitions() -> list[dict[str, Any]]:
    """Return all workflow templates."""
    with get_session() as session:
        workflows = session.scalars(
            select(WorkflowDefinition).order_by(WorkflowDefinition.workflow_key)
        ).all()
        return [
            {
                "workflow_key": workflow.workflow_key,
                "name": workflow.name,
                "steps": list(workflow.steps),
            }
            for workflow in workflows
        ]


def get_workflow_definition(workflow_key: str) -> dict[str, Any] | None:
    """Fetch one workflow template by key."""
    with get_session() as session:
        workflow = session.get(WorkflowDefinition, workflow_key)
        if not workflow:
            return None
        return {
            "workflow_key": workflow.workflow_key,
            "name": workflow.name,
            "steps": list(workflow.steps),
        }


def trigger_workflow(workflow_key: str, context: str | None = None) -> dict[str, Any]:
    """Persist a workflow execution and return its details."""
    with get_session() as session:
        workflow = session.get(WorkflowDefinition, workflow_key)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_key}")

        execution_id = f"WF-{uuid.uuid4().hex[:8].upper()}"
        triggered_at = datetime.now(timezone.utc)
        execution = WorkflowExecution(
            id=execution_id,
            workflow_key=workflow.workflow_key,
            status="Triggered",
            context=context,
            triggered_at=triggered_at,
        )
        session.add(execution)
        session.flush()

        steps = list(workflow.steps)
        return {
            "workflow_id": execution_id,
            "workflow_key": workflow.workflow_key,
            "name": workflow.name,
            "status": "Triggered",
            "steps": steps,
            "triggered_at": triggered_at.isoformat(),
            "context": context,
        }
