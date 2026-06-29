"""Pydantic models for enterprise action REST APIs."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ReportType = Literal["hr", "sales", "it", "leave"]
WorkflowKey = Literal[
    "onboarding",
    "offboarding",
    "access_provisioning",
    "leave_approval",
    "incident_escalation",
]
QuerySourceType = Literal["database", "file"]


TicketStatus = Literal["Open", "In Progress", "Resolved", "Closed"]
TicketPriority = Literal["Low", "Medium", "High"]


class CreateTicketRequest(BaseModel):
    """Payload for POST /tickets."""

    issue: str = Field(..., min_length=1, max_length=1000, examples=["VPN login fails every morning"])
    priority: TicketPriority = Field(default="Medium", examples=["High"])


class UpdateTicketRequest(BaseModel):
    """Payload for PATCH /tickets/{ticket_id}."""

    issue: Optional[str] = Field(default=None, min_length=1, max_length=1000, examples=["Updated issue description"])
    status: Optional[TicketStatus] = Field(default=None, examples=["In Progress"])
    priority: Optional[TicketPriority] = Field(default=None, examples=["High"])


class TicketResponse(BaseModel):
    """Support ticket record."""

    id: str = Field(examples=["INC-1001"])
    issue: str = Field(examples=["VPN login fails every morning"])
    status: str = Field(examples=["Open"])
    created_at: str = Field(examples=["2026-06-29T10:00:00+00:00"])
    updated_at: Optional[str] = Field(default=None, examples=["2026-06-29T11:30:00+00:00"])
    priority: Optional[str] = Field(default="Medium", examples=["High"])


class GenerateReportRequest(BaseModel):
    """Payload for POST /reports/generate."""

    report_type: ReportType = Field(default="hr", examples=["hr"])
    period: Optional[str] = Field(default="current_quarter", examples=["current_quarter"])


class ReportResponse(BaseModel):
    """Generated report metadata."""

    report_id: str
    title: str
    type: str
    generated_at: str
    metrics: dict[str, Any]
    format: str
    download_url: str
    period: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Employee directory record."""

    employee_id: str = Field(examples=["EMP-1001"])
    name: str = Field(examples=["Palash Joshi"])
    department: str = Field(examples=["Engineering"])
    role: str = Field(examples=["Senior Software Engineer"])
    email: str = Field(examples=["palash.joshi@company.com"])
    location: str = Field(examples=["Mumbai"])
    manager: str = Field(examples=["Jane Doe"])
    start_date: str = Field(examples=["2022-03-14"])
    status: str = Field(examples=["Active"])
    access_role: Optional[str] = Field(default=None, examples=["employee"])
    job_title: Optional[str] = Field(default=None, examples=["Senior Software Engineer"])


class CustomerResponse(BaseModel):
    """Customer account record."""

    customer_id: str
    name: str
    segment: str
    account_manager: str
    region: str
    mrr_usd: int
    status: str
    since: str


class QueryRequest(BaseModel):
    """Payload for POST /queries."""

    source_type: QuerySourceType = Field(default="database", examples=["database"])
    source_name: str = Field(default="employees", examples=["employees"])
    limit: int = Field(default=10, ge=1, le=100)


class QueryResponse(BaseModel):
    """Query execution result."""

    query_id: str
    source_type: str
    source_name: str
    row_count: int
    rows: list[dict[str, Any]]
    executed_at: str


class TriggerWorkflowRequest(BaseModel):
    """Payload for POST /workflows/trigger."""

    workflow_key: WorkflowKey = Field(default="onboarding", examples=["onboarding"])
    context: Optional[str] = Field(default=None, examples=["New hire starting Monday"])


class WorkflowResponse(BaseModel):
    """Triggered workflow status."""

    workflow_id: str
    workflow_key: str
    name: str
    status: str
    steps: list[str]
    triggered_at: str
    context: Optional[str] = None


class ProfileResponse(BaseModel):
    """Authenticated user profile with linked employee record."""

    user_id: str = Field(examples=["uuid"])
    email: str = Field(examples=["palash.joshi@company.com"])
    full_name: str = Field(examples=["Palash Joshi"])
    provider: str = Field(examples=["local"])
    employee: Optional[EmployeeResponse] = None
    workspace_role: str = Field(default="Workspace member", examples=["Employee"])
    job_title: Optional[str] = Field(default=None, examples=["Senior Software Engineer"])
    access_role: Optional[str] = Field(default=None, examples=["employee"])
