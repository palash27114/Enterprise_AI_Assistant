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


class CreateTicketRequest(BaseModel):
    """Payload for POST /tickets."""

    issue: str = Field(..., min_length=1, max_length=1000, examples=["VPN login fails every morning"])
    priority: Optional[str] = Field(default="Medium", examples=["High"])


class TicketResponse(BaseModel):
    """Support ticket record."""

    id: str
    issue: str
    status: str
    created_at: str
    priority: Optional[str] = None


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

    employee_id: str
    name: str
    department: str
    role: str
    email: str
    location: str
    manager: str
    start_date: str
    status: str


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
    """Simulated query execution result."""

    query_id: str
    source_type: str
    source_name: str
    row_count: int
    rows: list[dict[str, Any]]
    executed_at: str
    simulated: bool = True


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
    simulated: bool = True
    context: Optional[str] = None


class ProfileResponse(BaseModel):
    """Authenticated user profile with linked employee record."""

    user_id: str
    email: str
    full_name: str
    provider: str
    employee: Optional[EmployeeResponse] = None
    workspace_role: str = "Workspace member"
