"""Enterprise action REST APIs backed by PostgreSQL."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.enterprise_schemas import (
    CreateTicketRequest,
    CustomerResponse,
    EmployeeResponse,
    GenerateReportRequest,
    ProfileResponse,
    QueryRequest,
    QueryResponse,
    ReportResponse,
    TicketResponse,
    TriggerWorkflowRequest,
    UpdateTicketRequest,
    WorkflowResponse,
)
from app.services import action_service, ticket_service

router = APIRouter(tags=["Enterprise"])


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get authenticated user profile",
    description="Returns the signed-in user's account profile and linked employee record.",
)
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]) -> ProfileResponse:
    """Get the current user's profile."""
    result = action_service.get_profile(current_user)
    data = result["data"]
    employee = data.get("employee")
    return ProfileResponse(
        user_id=data["user_id"],
        email=data["email"],
        full_name=data["full_name"],
        provider=data["provider"],
        workspace_role=data.get("workspace_role", "Workspace member"),
        job_title=data.get("job_title"),
        access_role=data.get("access_role"),
        employee=EmployeeResponse(**employee) if employee else None,
    )


@router.post(
    "/tickets",
    response_model=TicketResponse,
    summary="Create a support ticket",
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: CreateTicketRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> TicketResponse:
    """Create a new support ticket."""
    result = action_service.create_ticket(
        issue=payload.issue,
        user_id=current_user.id,
        priority=payload.priority or "Medium",
    )
    ticket = result["data"]
    return TicketResponse(
        id=ticket["id"],
        issue=ticket["issue"],
        status=ticket["status"],
        created_at=ticket["created_at"],
        updated_at=ticket.get("updated_at"),
        priority=ticket.get("priority"),
    )


@router.get(
    "/tickets",
    response_model=list[TicketResponse],
    summary="List my support tickets",
)
async def list_my_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TicketResponse]:
    """List support tickets created by the signed-in user."""
    tickets = ticket_service.list_tickets_for_user(current_user.id)
    return [TicketResponse(**ticket) for ticket in tickets]


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Get a support ticket",
)
async def get_ticket(
    ticket_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> TicketResponse:
    """Fetch one ticket owned by the signed-in user."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket or ticket.get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return TicketResponse(**ticket)


@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="Update a support ticket",
)
async def update_ticket(
    ticket_id: str,
    payload: UpdateTicketRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> TicketResponse:
    """Update issue, status, or priority on a ticket you own."""
    if payload.issue is None and payload.status is None and payload.priority is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update: issue, status, or priority.",
        )
    try:
        ticket = ticket_service.update_ticket(
            ticket_id,
            current_user.id,
            issue=payload.issue,
            status=payload.status,
            priority=payload.priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return TicketResponse(**ticket)


@router.post(
    "/reports/generate",
    response_model=ReportResponse,
    summary="Generate an enterprise report",
)
async def generate_report(
    payload: GenerateReportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportResponse:
    """Generate an HR, sales, IT, or leave report from live database metrics."""
    _ = current_user
    result = action_service.generate_report(
        report_type=payload.report_type,
        period=payload.period or "current_quarter",
    )
    return ReportResponse(**result["data"])


@router.get(
    "/reports/types",
    summary="List available report types",
)
async def list_report_types(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[str]]:
    """Return supported report type keys."""
    _ = current_user
    return {"report_types": ["hr", "sales", "it", "leave"]}


@router.get(
    "/employees",
    response_model=list[EmployeeResponse],
    summary="List employees",
)
async def list_employees(
    current_user: Annotated[User, Depends(get_current_user)],
    search: Annotated[str | None, Query(description="Optional name or ID search")] = None,
) -> list[EmployeeResponse]:
    """List employee directory records visible to your role."""
    employees = action_service.list_employees(current_user, search=search)
    return [EmployeeResponse(**employee) for employee in employees]


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
)
async def get_employee(
    employee_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmployeeResponse:
    """Fetch one employee record by ID if visible to your role."""
    employee = action_service.get_employee(employee_id, user=current_user)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    return EmployeeResponse(**employee)


@router.get(
    "/customers",
    response_model=list[CustomerResponse],
    summary="List customers",
)
async def list_customers(
    current_user: Annotated[User, Depends(get_current_user)],
    search: Annotated[str | None, Query(description="Optional name or ID search")] = None,
) -> list[CustomerResponse]:
    """List customer accounts."""
    _ = current_user
    customers = action_service.list_customers(search=search)
    return [CustomerResponse(**customer) for customer in customers]


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
)
async def get_customer(
    customer_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> CustomerResponse:
    """Fetch one customer record by ID (e.g. CUST-5001)."""
    _ = current_user
    customer = action_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return CustomerResponse(**customer)


@router.post(
    "/queries",
    response_model=QueryResponse,
    summary="Query enterprise database tables",
)
async def run_query(
    payload: QueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> QueryResponse:
    """Query employees, customers, tickets, leave requests, or policies."""
    result = action_service.query_data(
        source_type=payload.source_type,
        source_name=payload.source_name,
        limit=payload.limit,
        user=current_user,
    )
    return QueryResponse(**result["data"])


@router.get(
    "/workflows",
    summary="List available workflows",
)
async def list_workflows(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, list[dict[str, object]]]:
    """Return workflow definitions that can be triggered."""
    _ = current_user
    return {"workflows": action_service.list_workflows()}


@router.post(
    "/workflows/trigger",
    response_model=WorkflowResponse,
    summary="Trigger a workflow",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_workflow(
    payload: TriggerWorkflowRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkflowResponse:
    """Trigger an enterprise workflow."""
    _ = current_user
    result = action_service.trigger_workflow(
        workflow_key=payload.workflow_key,
        context=payload.context,
    )
    return WorkflowResponse(**result["data"])
