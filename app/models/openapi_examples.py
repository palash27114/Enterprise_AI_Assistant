"""Example request/response payloads for Swagger documentation."""

from typing import Any

EMPLOYEE_EXAMPLE = {
    "employee_id": "EMP-1007",
    "name": "Palash Joshi",
    "department": "Engineering",
    "role": "Senior Software Engineer",
    "email": "palash.joshi@company.com",
    "location": "Bangalore",
    "manager": "Jane Doe",
    "start_date": "2020-01-15",
    "status": "Active",
    "access_role": "employee",
    "job_title": "Senior Software Engineer",
}

USER_EXAMPLE = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "palash.joshi@company.com",
    "full_name": "Palash Joshi",
    "provider": "local",
    "employee_id": "EMP-1007",
    "job_title": "Senior Software Engineer",
    "access_role": "employee",
    "access_role_label": "Employee",
}

TOKEN_EXAMPLE = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4.example",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": USER_EXAMPLE,
}

TICKET_EXAMPLE = {
    "id": "INC-1001",
    "issue": "VPN login fails every morning",
    "status": "Open",
    "priority": "High",
    "created_at": "2026-06-29T10:00:00+00:00",
    "updated_at": "2026-06-29T10:00:00+00:00",
}

# Keyed by (HTTP method, OpenAPI path template)
OPERATION_EXAMPLES: dict[tuple[str, str], dict[str, Any]] = {
    ("get", "/health"): {
        "responses": {
            "200": {"status": "ok", "database": "ok"},
            "503": {"status": "degraded", "database": "unavailable"},
        },
    },
    ("post", "/auth/register"): {
        "request": {
            "email": "palash.joshi@company.com",
            "password": "securepass123",
            "full_name": "Palash Joshi",
        },
        "responses": {
            "200": TOKEN_EXAMPLE,
            "400": {"detail": "An account with this email already exists."},
        },
    },
    ("post", "/auth/login"): {
        "request": {
            "email": "palash.joshi@company.com",
            "password": "securepass123",
        },
        "responses": {
            "200": TOKEN_EXAMPLE,
            "401": {"detail": "Invalid email or password."},
        },
    },
    ("post", "/auth/refresh"): {
        "request": {"refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4.example"},
        "responses": {
            "200": TOKEN_EXAMPLE,
            "401": {"detail": "Invalid or expired refresh token."},
        },
    },
    ("post", "/auth/logout"): {
        "request": {"refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4.example"},
        "responses": {"200": {"message": "Logged out successfully."}},
    },
    ("get", "/auth/me"): {
        "responses": {"200": USER_EXAMPLE},
    },
    ("post", "/auth/change-password"): {
        "request": {
            "current_password": "securepass123",
            "new_password": "newsecurepass456",
        },
        "responses": {
            "200": {"message": "Password updated successfully."},
            "400": {"detail": "Current password is incorrect."},
        },
    },
    ("post", "/auth/forgot-password"): {
        "request": {"email": "palash.joshi@company.com"},
        "responses": {
            "200": {
                "message": "If an account exists for that email, password reset instructions have been sent.",
                "reset_url": "http://localhost:5173/reset-password?token=example-reset-token",
            },
        },
    },
    ("post", "/auth/reset-password"): {
        "request": {
            "token": "example-reset-token",
            "new_password": "newsecurepass456",
        },
        "responses": {
            "200": {
                "message": "Password reset successfully. You can sign in with your new password.",
            },
            "400": {"detail": "Invalid or expired password reset link."},
        },
    },
    ("get", "/auth/google/login"): {
        "responses": {
            "200": {"redirect": "https://accounts.google.com/o/oauth2/v2/auth?..."},
        },
    },
    ("get", "/auth/google/callback"): {
        "responses": {
            "200": {"redirect": "http://localhost:5173/oauth/callback?access_token=..."},
            "422": {"detail": "Invalid authentication response."},
        },
    },
    ("get", "/auth/github/login"): {
        "responses": {
            "200": {"redirect": "https://github.com/login/oauth/authorize?..."},
        },
    },
    ("get", "/auth/github/callback"): {
        "responses": {
            "200": {"redirect": "http://localhost:5173/oauth/callback?access_token=..."},
            "422": {"detail": "Invalid authentication response."},
        },
    },
    ("get", "/agents"): {
        "responses": {
            "200": {
                "default_agent": "gemini",
                "agents": [
                    {
                        "id": "gemini",
                        "name": "Google Gemini",
                        "model": "gemini-2.5-flash",
                        "available": True,
                        "is_default": True,
                        "healthy": True,
                    },
                    {
                        "id": "openai",
                        "name": "OpenAI",
                        "model": "gpt-4o-mini",
                        "available": True,
                        "is_default": False,
                        "healthy": False,
                    },
                ],
            },
        },
    },
    ("post", "/ask"): {
        "request": {"question": "Generate an HR headcount report for this quarter."},
        "responses": {
            "200": {
                "response": "Generated HR Headcount Report (RPT-A1B2C3D4). Summary — total employees: 248.",
                "action": "generate_report",
                "ticket_id": None,
                "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "Completed",
                "agent": "gemini",
                "data": {"report_id": "RPT-A1B2C3D4", "type": "hr"},
            },
            "401": {"detail": "Authentication required. Please log in."},
            "422": {"detail": "Question cannot be empty or whitespace only."},
        },
    },
    ("get", "/conversations"): {
        "responses": {
            "200": [
                {
                    "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "title": "Generate an HR headcount report",
                    "preview": "Generated HR Headcount Report...",
                    "message_count": 4,
                    "updated_at": "2026-06-29T12:00:00+00:00",
                }
            ],
        },
    },
    ("get", "/conversations/{conversation_id}"): {
        "responses": {
            "200": {
                "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "title": "Generate an HR headcount report",
                "updated_at": "2026-06-29T12:00:00+00:00",
                "messages": [
                    {"role": "user", "content": "Generate an HR headcount report."},
                    {"role": "assistant", "content": "Generated HR Headcount Report (RPT-A1B2C3D4)."},
                ],
            },
            "404": {"detail": "Conversation not found."},
        },
    },
    ("get", "/profile"): {
        "responses": {
            "200": {
                "user_id": USER_EXAMPLE["id"],
                "email": USER_EXAMPLE["email"],
                "full_name": USER_EXAMPLE["full_name"],
                "provider": "local",
                "workspace_role": "Employee",
                "job_title": "Senior Software Engineer",
                "access_role": "employee",
                "employee": EMPLOYEE_EXAMPLE,
            },
        },
    },
    ("post", "/tickets"): {
        "request": {
            "issue": "VPN login fails every morning",
            "priority": "High",
        },
        "responses": {"201": TICKET_EXAMPLE},
    },
    ("get", "/tickets"): {
        "responses": {"200": [TICKET_EXAMPLE]},
    },
    ("get", "/tickets/{ticket_id}"): {
        "responses": {
            "200": TICKET_EXAMPLE,
            "404": {"detail": "Ticket not found."},
        },
    },
    ("patch", "/tickets/{ticket_id}"): {
        "request": {
            "issue": "VPN still failing after reboot",
            "status": "In Progress",
            "priority": "High",
        },
        "responses": {
            "200": {
                **TICKET_EXAMPLE,
                "issue": "VPN still failing after reboot",
                "status": "In Progress",
            },
            "404": {"detail": "Ticket not found."},
        },
    },
    ("post", "/reports/generate"): {
        "request": {"report_type": "hr", "period": "current_quarter"},
        "responses": {
            "200": {
                "report_id": "RPT-A1B2C3D4",
                "title": "HR Headcount Report",
                "type": "hr",
                "generated_at": "2026-06-29T10:00:00+00:00",
                "metrics": {
                    "total_employees": 100,
                    "open_roles": 12,
                    "avg_tenure_years": 3.4,
                    "departments": 8,
                },
                "format": "pdf",
                "download_url": "/mock/reports/RPT-A1B2C3D4.pdf",
                "period": "current_quarter",
            },
        },
    },
    ("get", "/reports/types"): {
        "responses": {"200": {"report_types": ["hr", "sales", "it", "leave"]}},
    },
    ("get", "/employees"): {
        "responses": {"200": [EMPLOYEE_EXAMPLE]},
    },
    ("get", "/employees/{employee_id}"): {
        "responses": {
            "200": EMPLOYEE_EXAMPLE,
            "404": {"detail": "Employee not found."},
        },
    },
    ("get", "/customers"): {
        "responses": {
            "200": [
                {
                    "customer_id": "CUST-5001",
                    "name": "Acme Corporation",
                    "segment": "Enterprise",
                    "account_manager": "Maria Garcia",
                    "region": "North America",
                    "mrr_usd": 12500,
                    "status": "Active",
                    "since": "2020-04-12",
                }
            ],
        },
    },
    ("get", "/customers/{customer_id}"): {
        "responses": {
            "200": {
                "customer_id": "CUST-5001",
                "name": "Acme Corporation",
                "segment": "Enterprise",
                "account_manager": "Maria Garcia",
                "region": "North America",
                "mrr_usd": 12500,
                "status": "Active",
                "since": "2020-04-12",
            },
            "404": {"detail": "Customer not found."},
        },
    },
    ("post", "/queries"): {
        "request": {
            "source_type": "database",
            "source_name": "employees",
            "limit": 10,
        },
        "responses": {
            "200": {
                "query_id": "QRY-A1B2C3D4",
                "source_type": "database",
                "source_name": "employees",
                "row_count": 2,
                "rows": [EMPLOYEE_EXAMPLE],
                "executed_at": "2026-06-29T10:00:00+00:00",
            },
        },
    },
    ("get", "/workflows"): {
        "responses": {
            "200": {
                "workflows": [
                    {
                        "key": "onboarding",
                        "name": "Employee Onboarding",
                        "description": "Provision accounts and equipment for new hires.",
                    }
                ],
            },
        },
    },
    ("post", "/workflows/trigger"): {
        "request": {
            "workflow_key": "onboarding",
            "context": "New hire starting Monday",
        },
        "responses": {
            "202": {
                "workflow_id": "WF-A1B2C3D4",
                "workflow_key": "onboarding",
                "name": "Employee Onboarding",
                "status": "Triggered",
                "steps": [
                    "Validate request",
                    "Manager approval",
                    "IT provisioning",
                    "Audit log",
                ],
                "triggered_at": "2026-06-29T10:00:00+00:00",
                "context": "New hire starting Monday",
            },
        },
    },
}

# Default examples for common error responses on protected routes
DEFAULT_AUTH_ERROR = {"detail": "Authentication required. Please log in."}

PROTECTED_PATH_PREFIXES = (
    "/ask",
    "/conversations",
    "/profile",
    "/tickets",
    "/reports",
    "/employees",
    "/customers",
    "/queries",
    "/workflows",
)
