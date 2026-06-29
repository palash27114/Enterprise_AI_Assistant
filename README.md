# Enterprise AI Assistant

A production-ready, full-stack enterprise assistant that answers HR, IT, and operations questions and performs business actions through a Python API and React chat UI.

Built with **Python 3.11+**, **FastAPI**, **PostgreSQL**, **React (Vite)**, **Docker**, and configurable **OpenAI** or **Google Gemini** LLM providers.

---

## Project Overview

The assistant exposes `POST /ask` as the primary chat endpoint. For each message it:

1. **Validates** the request (Pydantic guardrails on question length and content)
2. **Authenticates** the user (JWT required)
3. **Loads conversation memory** from PostgreSQL (per-user, multi-turn)
4. **Calls the LLM with tool definitions** — the model decides whether to answer directly or invoke an enterprise action
5. **Executes the chosen action** via the same service layer as the documented REST APIs (tickets, reports, lookups, queries, workflows)
6. **Returns a structured JSON response** with `action`, `data`, `conversation_id`, and optional `ticket_id`

**All enterprise data lives in PostgreSQL** — 100-employee org hierarchy, customers, leave requests, workflow definitions, policies, tickets, and user accounts. There is no separate mock data layer.

---

## Features

| Area | Capability |
|------|------------|
| **AI chat** | `POST /ask` with OpenAI or Gemini tool-calling |
| **Business actions** | Create ticket, generate report, fetch employee/customer, query DB tables, trigger workflow |
| **Tool routing** | LLM chooses tools dynamically (not keyword-based routing) |
| **Conversation memory** | PostgreSQL-backed history; sidebar UI to resume past chats |
| **Enterprise REST APIs** | Same actions exposed on Swagger under the **Enterprise** tag |
| **Org hierarchy** | 100 seeded employees; CEO → directors → managers → staff |
| **Role-based visibility** | HR/executive see all; managers see direct reports; employees see self |
| **Authentication** | Email/password register & login, Google OAuth, GitHub OAuth, JWT + refresh tokens |
| **Password management** | Change password (logged in), forgot/reset password (local accounts) |
| **Ticket management** | Create, list, get, and update tickets (issue, status, priority) |
| **Live reports** | HR, sales, IT, and leave metrics computed from real DB aggregates |
| **Provider fallback** | Auto-switches OpenAI ↔ Gemini on quota errors |
| **Input validation** | Rejects empty, whitespace-only, or >1000 character questions |
| **Error handling** | LLM failures return `action: "error"` without crashing the API |
| **Web UI** | React chat app with auth, agent selector, chat history sidebar, account modal |
| **API docs** | Swagger UI at `/docs` (example-only request/response bodies) |
| **Docker** | Production stack (nginx + API + frontend + PostgreSQL) and dev stack with hot reload |
| **DB migrations** | Liquibase-compatible changelogs applied automatically on API startup |

---

## Architecture

### System deployment (production)

```mermaid
flowchart TB
    subgraph Client["Client"]
        Browser["Browser<br/>React Chat UI"]
    end

    subgraph Docker["Docker Compose Stack"]
        Nginx["nginx :80<br/>Reverse proxy"]
        Frontend["frontend<br/>Static React build"]
        API["api :8000<br/>FastAPI + Uvicorn"]
        PG[("postgres :5432<br/>PostgreSQL 16")]
    end

    subgraph External["External Services"]
        OpenAI["OpenAI API"]
        Gemini["Google Gemini API"]
        GoogleOAuth["Google OAuth"]
        GitHubOAuth["GitHub OAuth"]
    end

    Browser --> Nginx
    Nginx -->|"/" static assets| Frontend
    Nginx -->|"/ask, /auth, /conversations,<br/>/tickets, /docs, …"| API
    API --> PG
    API --> OpenAI
    API --> Gemini
    API --> GoogleOAuth
    API --> GitHubOAuth
```

### Development deployment

```mermaid
flowchart LR
    Browser["Browser :5173"] -->|Vite proxy| API["FastAPI :8000"]
    API --> PG[("PostgreSQL :5432")]
    API --> LLM["OpenAI / Gemini"]
```

In dev mode the React app runs on port **5173** and proxies API calls to the backend. Swagger is available at `http://localhost:5173/docs` (proxied) or `http://localhost:8000/docs` (direct).

---

### AI request workflow

```mermaid
sequenceDiagram
    participant U as User / React UI
    participant A as POST /ask
    participant M as memory_service
    participant L as llm_service
    participant LLM as OpenAI / Gemini
    participant T as assistant_tools
    participant S as action_service
    participant DB as PostgreSQL

    U->>A: question + Bearer token + optional X-Conversation-Id
    A->>M: get_or_create_conversation()
    M->>DB: load / create conversation
    A->>M: add_message(user)
    A->>M: get_message_history()
    A->>L: process_assistant_request(history, user)
    L->>LLM: chat completion + tool definitions
    alt Model calls a tool
        LLM-->>L: function_call (e.g. create_support_ticket)
        L->>T: execute_tool()
        T->>S: action_service (same as REST APIs)
        S->>DB: read / write enterprise data
        S-->>T: structured result
        T-->>L: normalized response
    else Model answers directly
        LLM-->>L: plain text answer
    end
    L-->>A: response + action + data
    A->>M: add_message(assistant)
    A-->>U: AskResponse JSON
```

---

### Application layers

```mermaid
flowchart TB
    subgraph Presentation["Presentation"]
        UI["React UI<br/>LoginPage, ChatSidebar, ChatWindow"]
        Swagger["Swagger / ReDoc"]
    end

    subgraph API["API Layer (FastAPI routes)"]
        Ask["/ask, /agents"]
        Auth["/auth/*"]
        Conv["/conversations"]
        Ent["/profile, /tickets, /reports,<br/>/employees, /customers,<br/>/queries, /workflows"]
        Health["/health"]
    end

    subgraph Services["Service Layer"]
        LLM["llm_service<br/>tool-calling + fallback"]
        Tools["assistant_tools"]
        Actions["action_service"]
        Memory["memory_service"]
        AuthSvc["auth_service"]
        Agents["agent_service"]
        Emp["employee_service"]
        Cust["customer_service"]
        Ticket["ticket_service"]
        Report["report_service"]
        Query["query_service"]
        Workflow["workflow_service"]
    end

    subgraph Data["Data"]
        ORM["SQLAlchemy models"]
        PG[("PostgreSQL")]
    end

    UI --> Ask & Auth & Conv
    Swagger --> Ent & Ask & Auth
    Ask --> LLM & Memory
    Conv --> Memory
    Auth --> AuthSvc
    Ent --> Actions
    LLM --> Tools
    Tools --> Actions
    Actions --> Emp & Cust & Ticket & Report & Query & Workflow
    Memory --> ORM
    AuthSvc --> ORM
    Emp & Cust & Ticket & Report & Query & Workflow --> ORM
    ORM --> PG
```

---

### Docker services

| Service | Role |
|---------|------|
| `postgres` | PostgreSQL 16 — all application and enterprise data |
| `api` | FastAPI application (Uvicorn; runs DB migrations on startup) |
| `frontend` | React chat UI (Vite dev server in dev; static nginx build in prod) |
| `nginx` | Reverse proxy — single entry point on port 80 (production only) |

### Database migrations (Liquibase-compatible, on API startup)

Schema is **not** created by a separate Liquibase container. When the API starts, it runs migrations from `db/changelog/` before serving requests:

| Changeset | Purpose |
|-----------|---------|
| `001-initial-schema.sql` | Core tables: `employees`, `users`, `refresh_tokens`, `tickets`, `conversations`, `messages` |
| `003-seed-org-hierarchy.sql` | Seeds 100 employees with org hierarchy and links users by email |
| `004-password-reset-tokens.sql` | `password_reset_tokens` table for forgot-password flow |
| `005-enterprise-reference-data.sql` | `customers`, `leave_requests`, `workflow_definitions`, `workflow_executions`, `policies` + seed data |

Tracking uses standard Liquibase tables: `databasechangelog` and `databasechangeloglock`.

To reset and re-apply from scratch:

```bash
make docker-reset-db
make docker-dev
```

To regenerate the 100-employee seed:

```bash
python3 scripts/generate_org_seed.py
```

---

## Evolution from basic implementation

| Basic version | Current implementation |
|---------------|------------------------|
| Keyword / regex intent routing | **LLM tool-calling** — model picks the right enterprise action |
| In-memory or file storage | **PostgreSQL** for conversations, users, tickets, and all enterprise data |
| Static mock employee list | **100-employee org hierarchy** with role-based directory visibility |
| Hardcoded report numbers | **Live reports** computed from DB aggregates (headcount, MRR, tickets, leave) |
| Single `POST /ask` only | **Full Enterprise REST API** on Swagger; chat tools call the same handlers |
| One LLM provider | **OpenAI + Gemini** with UI agent selector and quota fallback |
| Unauthenticated API | **JWT auth** + Google/GitHub OAuth; chat history scoped per user |
| Plain text responses | Structured `action`, `data`, `ticket_id`, `status`, `agent` fields |

---

## Assignment alignment (60-minute build challenge)

| Requirement | Status |
|-------------|--------|
| `POST /ask` with question processing | ✅ |
| Business actions (ticket, report, employee/customer, query, workflow) | ✅ |
| Conversation memory | ✅ |
| API / tool calling | ✅ |
| Error handling & fallback | ✅ |
| Request validation & guardrails | ✅ |
| Document retrieval (simple RAG) | ⏳ Not yet implemented — optional enhancement |

---

## Demo accounts

Seed data includes employees you can register with (email/password) to test role-based access:

| Email | Role | Sees in directory |
|-------|------|-------------------|
| `ceo@company.com` | Executive | All 100 employees |
| `alex.chen@company.com` | HR | All 100 employees |
| `jane.doe@company.com` | Manager | Self + direct reports |
| `palash.joshi@company.com` | Employee | Self only |

Register with any `@company.com` email from the seed to link your user account to the employee record automatically.

---

## Project Structure

```
enterprise-ai-assistant/
│
├── app/
│   ├── main.py                     # FastAPI app factory, CORS, custom Swagger
│   ├── core/
│   │   ├── config.py               # Environment & system prompt
│   │   ├── logging.py
│   │   ├── security.py             # JWT, password hashing
│   │   └── openapi_custom.py       # Swagger example-only schema
│   ├── api/
│   │   ├── router.py
│   │   ├── dependencies.py         # get_current_user
│   │   └── routes/
│   │       ├── ask.py              # POST /ask, GET /agents
│   │       ├── auth.py             # Register, login, OAuth, password reset
│   │       ├── conversations.py    # Chat history list & detail
│   │       ├── enterprise.py       # Tickets, reports, lookups, queries, workflows
│   │       └── health.py
│   ├── db/
│   │   ├── models.py               # User, Employee, Ticket, Customer, …
│   │   ├── session.py              # SQLAlchemy engine & init_db()
│   │   └── migrations.py           # Liquibase-compatible migration runner
│   ├── models/
│   │   ├── schemas.py              # AskRequest, AskResponse, auth schemas
│   │   ├── enterprise_schemas.py
│   │   ├── openapi.py              # Swagger metadata & tags
│   │   └── openapi_examples.py     # Curated Swagger examples
│   ├── services/
│   │   ├── llm_service.py          # OpenAI / Gemini + tool-calling + fallback
│   │   ├── assistant_tools.py      # Tool definitions & execution
│   │   ├── action_service.py       # Enterprise action orchestration
│   │   ├── employee_service.py     # Org hierarchy & visibility rules
│   │   ├── customer_service.py
│   │   ├── ticket_service.py
│   │   ├── report_service.py       # Live DB-backed reports
│   │   ├── query_service.py        # Query employees, customers, tickets, etc.
│   │   ├── workflow_service.py
│   │   ├── leave_service.py
│   │   ├── memory_service.py
│   │   ├── auth_service.py
│   │   └── agent_service.py
│   └── data/
│       └── org_employees.json      # Source for seed script
│
├── db/changelog/                   # SQL migrations (applied on API startup)
├── frontend/                       # React + TypeScript + Vite
├── docker/                         # API, frontend, nginx, postgres
├── scripts/generate_org_seed.py    # Regenerate 100-employee SQL seed
├── docker-compose.yml              # Production stack
├── docker-compose.dev.yml          # Development stack (hot reload)
├── Makefile
├── requirements.txt
└── .env.example
```

---

## API Reference

### Assistant

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ask` | Bearer | Send a message; LLM routes to tools or direct answer |
| `GET` | `/agents` | No | List configured LLM providers and health |
| `GET` | `/conversations` | Bearer | List user's chat history (newest first) |
| `GET` | `/conversations/{id}` | Bearer | Load full message history for one chat |

### Enterprise (also invoked by AI tools)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/profile` | Signed-in user profile + linked employee record |
| `POST` | `/tickets` | Create support ticket |
| `GET` | `/tickets` | List your tickets |
| `GET` | `/tickets/{id}` | Get one ticket |
| `PATCH` | `/tickets/{id}` | Update issue, status, or priority |
| `POST` | `/reports/generate` | Generate HR / sales / IT / leave report (live DB metrics) |
| `GET` | `/reports/types` | List available report types |
| `GET` | `/employees` | List employees visible to your role |
| `GET` | `/employees/{id}` | Get employee by ID |
| `GET` | `/customers` | List customer accounts |
| `GET` | `/customers/{id}` | Get customer by ID |
| `POST` | `/queries` | Query enterprise tables (employees, customers, tickets, leave, policies) |
| `GET` | `/workflows` | List workflow definitions |
| `POST` | `/workflows/trigger` | Trigger and persist a workflow execution |

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Email/password login |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | Revoke refresh token |
| `POST` | `/auth/change-password` | Change password (authenticated, local accounts) |
| `POST` | `/auth/forgot-password` | Request password reset link |
| `POST` | `/auth/reset-password` | Reset password with one-time token |
| `GET` | `/auth/me` | Current user profile |
| `GET` | `/auth/google/login` | Start Google OAuth |
| `GET` | `/auth/github/login` | Start GitHub OAuth |

Interactive documentation: **Swagger** at `/docs` · **ReDoc** at `/redoc`

---

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Add OPENAI_API_KEY and/or GEMINI_API_KEY, set JWT_SECRET_KEY for production

# Development (hot reload)
make docker-dev

# Production
make docker-up
```

| Mode | Chat UI | Swagger |
|------|---------|---------|
| **Dev** | http://localhost:5173 | http://localhost:5173/docs or http://localhost:8000/docs |
| **Prod** | http://localhost | http://localhost/docs |

### Local (without Docker)

**Prerequisites:** Python 3.11+, Node 20+, PostgreSQL running locally

```bash
# API
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make dev

# Frontend (separate terminal)
make frontend-install
make frontend-dev
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | If using OpenAI | — | OpenAI API key |
| `GEMINI_API_KEY` | If using Gemini | — | Google Gemini API key |
| `LLM_PROVIDER` | No | `openai` | Default provider: `openai` or `gemini` |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model |
| `DATABASE_URL` | No | built from `POSTGRES_*` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes (prod) | — | Secret for signing JWTs |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES` | No | `60` | Forgot-password token lifetime |
| `EXPOSE_PASSWORD_RESET_URL` | No | `false` | Dev: return reset link in API response |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | For Google login | — | Google OAuth credentials |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | For GitHub login | — | GitHub OAuth credentials |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL for OAuth redirects |
| `BACKEND_URL` | No | `http://localhost:8000` | Backend URL for OAuth callbacks |
| `CORS_ORIGINS` | No | localhost origins | Allowed CORS origins (comma-separated) |
| `APP_WORKERS` | No | `2` | Uvicorn workers (production) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `NGINX_PORT` | No | `80` | Host port for nginx (production) |
| `API_PORT` | No | `8000` | Host port for API (dev) |
| `FRONTEND_PORT` | No | `5173` | Host port for Vite (dev) |

---

## API Examples

### Register and ask a question

```bash
# Register as CEO (links to seeded employee record)
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"ceo@company.com","password":"securepass123","full_name":"Riley Morgan"}'

# Login (or use access_token from register response)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ceo@company.com","password":"securepass123"}' \
  | jq -r '.access_token')

# Ask the assistant — HR headcount report (live DB metrics)
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question": "Generate an HR headcount report for this quarter."}'

# Query employee count
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question": "How many people do we have in the company right now?"}'
```

### Continue a conversation

```bash
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Conversation-Id: <conversation_id_from_previous_response>" \
  -d '{"question": "My laptop will not start — create a high-priority support ticket."}'
```

### List chat history

```bash
curl -s http://localhost:8000/conversations \
  -H "Authorization: Bearer $TOKEN"
```

---

## Sample Responses

### Direct AI answer

```json
{
  "response": "Our leave policy typically includes paid annual leave, sick leave, and company holidays...",
  "action": "ai_response",
  "ticket_id": null,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": null,
  "agent": "gemini",
  "data": null
}
```

### Tool action — ticket created

```json
{
  "response": "Support ticket INC-1001 created successfully.",
  "action": "create_ticket",
  "ticket_id": "INC-1001",
  "conversation_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "Open",
  "agent": "gemini",
  "data": {
    "id": "INC-1001",
    "issue": "Laptop will not start",
    "status": "Open",
    "priority": "High"
  }
}
```

### Tool action — data query (100 employees)

```json
{
  "response": "Query QRY-A1B2C3D4 executed against database `employees`. Returned 100 record(s).",
  "action": "query_data",
  "ticket_id": null,
  "conversation_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "status": "Success",
  "agent": "gemini",
  "data": {
    "query_id": "QRY-A1B2C3D4",
    "source_type": "database",
    "source_name": "employees",
    "row_count": 100,
    "rows": []
  }
}
```

---

## Makefile Commands

```bash
make help             # List all commands
make dev              # Run API locally with hot reload
make frontend-dev     # Run React dev server
make docker-dev       # Full dev stack in Docker
make docker-up        # Production stack
make docker-down      # Stop containers
make docker-logs      # Tail logs
make docker-reset-db  # Wipe DB volume and restart (re-runs migrations)
make health           # Ping /health endpoint
```

---

## License

MIT
