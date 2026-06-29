"""Mock enterprise data for simulated assistant actions."""

from datetime import datetime, timezone

EMPLOYEES = [
    {
        "employee_id": "EMP-1001",
        "name": "Palash Joshi",
        "department": "Engineering",
        "role": "Senior Software Engineer",
        "email": "palash.joshi@company.com",
        "location": "Mumbai",
        "manager": "Jane Doe",
        "start_date": "2022-03-14",
        "status": "Active",
    },
    {
        "employee_id": "EMP-1002",
        "name": "Jane Doe",
        "department": "Engineering",
        "role": "Engineering Manager",
        "email": "jane.doe@company.com",
        "location": "Mumbai",
        "manager": "Alex Chen",
        "start_date": "2019-08-01",
        "status": "Active",
    },
    {
        "employee_id": "EMP-1003",
        "name": "Alex Chen",
        "department": "HR",
        "role": "HR Director",
        "email": "alex.chen@company.com",
        "location": "Bangalore",
        "manager": "CEO Office",
        "start_date": "2017-01-10",
        "status": "Active",
    },
    {
        "employee_id": "EMP-1004",
        "name": "Maria Garcia",
        "department": "Customer Success",
        "role": "Account Manager",
        "email": "maria.garcia@company.com",
        "location": "Remote",
        "manager": "Sam Wilson",
        "start_date": "2021-06-21",
        "status": "Active",
    },
]

CUSTOMERS = [
    {
        "customer_id": "CUST-5001",
        "name": "Acme Corporation",
        "segment": "Enterprise",
        "account_manager": "Maria Garcia",
        "region": "North America",
        "mrr_usd": 12500,
        "status": "Active",
        "since": "2020-04-12",
    },
    {
        "customer_id": "CUST-5002",
        "name": "Globex Industries",
        "segment": "Mid-Market",
        "account_manager": "Sam Wilson",
        "region": "Europe",
        "mrr_usd": 4800,
        "status": "Active",
        "since": "2022-09-03",
    },
    {
        "customer_id": "CUST-5003",
        "name": "Initech Labs",
        "segment": "SMB",
        "account_manager": "Maria Garcia",
        "region": "APAC",
        "mrr_usd": 950,
        "status": "Trial",
        "since": "2025-11-18",
    },
]

REPORT_TEMPLATES = {
    "hr": {
        "title": "HR Headcount Report",
        "metrics": {
            "total_employees": 248,
            "open_roles": 12,
            "avg_tenure_years": 3.4,
            "departments": 6,
        },
    },
    "sales": {
        "title": "Sales Performance Report",
        "metrics": {
            "total_mrr_usd": 186750,
            "active_customers": 42,
            "new_deals_qtd": 7,
            "churn_rate_pct": 1.8,
        },
    },
    "it": {
        "title": "IT Incident Report",
        "metrics": {
            "open_tickets": 18,
            "resolved_this_week": 34,
            "avg_resolution_hours": 6.2,
            "critical_incidents": 1,
        },
    },
    "leave": {
        "title": "Leave Utilization Report",
        "metrics": {
            "pending_requests": 9,
            "approved_this_month": 27,
            "avg_days_taken": 12.5,
            "team_coverage_pct": 94,
        },
    },
}

DATABASE_TABLES = {
    "employees": EMPLOYEES,
    "customers": CUSTOMERS,
    "tickets": [
        {"ticket_id": "INC-1042", "issue": "VPN login failure", "status": "Open", "priority": "High"},
        {"ticket_id": "INC-1041", "issue": "Outlook sync delay", "status": "In Progress", "priority": "Medium"},
        {"ticket_id": "INC-1040", "issue": "Laptop battery drain", "status": "Resolved", "priority": "Low"},
    ],
    "leave_requests": [
        {"request_id": "LV-301", "employee": "Palash Joshi", "days": 3, "status": "Approved"},
        {"request_id": "LV-302", "employee": "Jane Doe", "days": 5, "status": "Pending"},
    ],
}

FILE_SOURCES = {
    "employees.csv": EMPLOYEES,
    "customers.csv": CUSTOMERS,
    "policies.txt": [
        {"section": "Leave Policy", "summary": "20 days annual leave, 10 sick days"},
        {"section": "Remote Work", "summary": "Hybrid schedule up to 3 days remote"},
        {"section": "Expense Policy", "summary": "Pre-approval required above $500"},
    ],
}

WORKFLOW_DEFINITIONS = {
    "onboarding": {
        "name": "Employee Onboarding",
        "steps": ["Create accounts", "Assign equipment", "Schedule orientation", "Grant app access"],
    },
    "offboarding": {
        "name": "Employee Offboarding",
        "steps": ["Revoke access", "Collect equipment", "Final payroll", "Exit interview"],
    },
    "access_provisioning": {
        "name": "Access Provisioning",
        "steps": ["Validate request", "Manager approval", "IT provisioning", "Audit log"],
    },
    "leave_approval": {
        "name": "Leave Approval",
        "steps": ["Submit request", "Manager review", "HR confirmation", "Calendar update"],
    },
    "incident_escalation": {
        "name": "Incident Escalation",
        "steps": ["Triage ticket", "Notify on-call", "Create war room", "Post-incident review"],
    },
}


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()
