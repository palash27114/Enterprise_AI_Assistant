# Enterprise AI Assistant

A production-ready REST API that powers an enterprise assistant capable of answering HR, IT, and policy questions while automatically creating support tickets when users report incidents.

Built with **Python 3.11+**, **FastAPI**, **Docker**, and configurable **OpenAI** or **Google Gemini** LLM providers.

---

## Project Overview

The Enterprise AI Assistant exposes a single primary endpoint, `POST /ask`, that:

1. Validates incoming questions
2. Persists conversation history to JSON storage
3. Routes intent between general AI Q&A and support ticket creation
4. Executes the appropriate action and returns a structured JSON response

The application is modular, containerized, and designed for both local development and production deployment.

---

## Features

- **Single REST endpoint** — `POST /ask` for all interactions
- **Intent routing** — Detects ticket-related keywords and creates support tickets automatically
- **LLM-powered answers** — Uses OpenAI or Gemini for HR, IT, and policy questions
- **Conversation memory** — Stores and replays message history for contextual responses
- **PostgreSQL persistence** — Tickets and conversations stored in PostgreSQL
- **Input validation** — Rejects empty, whitespace-only, or overly long questions
- **Graceful error handling** — LLM failures never crash the API
- **Structured logging** — Request, intent, ticket, LLM, and error events
- **Auto-generated API docs** — Available at `/docs` and `/redoc`
- **Web chat UI** — React frontend for asking questions and creating tickets
- **Authentication** — Email/password, Google OAuth, GitHub OAuth with JWT + refresh tokens
- **Protected AI chat** — Only logged-in users can call `POST /ask`
- **Docker production stack** — Frontend + API + nginx + PostgreSQL

---

## Architecture

```
Browser (React UI)
    │
nginx (port 80)
 ┌────────┴────────┐
 │                 │
Frontend        FastAPI API
(static)        (port 8000)
                     │
              PostgreSQL
```

### Docker services

| Service | Role |
|---------|------|
| `postgres` | PostgreSQL 16 database for tickets and conversations |
| `api` | FastAPI application (multi-worker uvicorn) |
| `frontend` | React chat UI (static build served by nginx) |
| `nginx` | Reverse proxy and public entry point |

---

## Project Structure

```
enterprise-ai-assistant/
│
├── app/                          # Application package
│   ├── main.py                   # FastAPI app factory
│   ├── core/
│   │   ├── config.py             # Environment configuration
│   │   └── logging.py            # Logging setup
│   ├── api/
│   │   ├── router.py             # Route aggregation
│   │   └── routes/
│   │       ├── ask.py            # POST /ask
│   │       └── health.py         # GET /health
│   ├── models/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── openapi.py            # Swagger metadata
│   └── services/
│       ├── intent.py             # Intent detection
│       ├── llm_service.py        # OpenAI / Gemini integration
│       ├── ticket_service.py     # Ticket management
│       └── memory_service.py     # Conversation persistence
│   └── db/
│       ├── models.py             # SQLAlchemy ORM models
│       └── session.py            # Database engine and sessions
│
├── docker/
│   ├── api/
│   │   ├── Dockerfile            # Production API image
│   │   └── entrypoint.sh         # Container startup script
│   ├── nginx/
│   │   ├── Dockerfile            # Nginx reverse proxy
│   │   └── nginx.conf            # Proxy configuration
│   └── postgres/
│       └── init.sql              # Database schema
│   └── frontend/
│       └── Dockerfile            # Frontend production image
│
├── frontend/                     # React chat UI (Vite + TypeScript)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/client.ts
│   │   └── components/
│   └── package.json
│
├── main.py                       # Uvicorn entry point
├── docker-compose.yml            # Production stack
├── docker-compose.dev.yml        # Development stack
├── Makefile                      # Common commands
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## Installation (Local)

### Prerequisites

- Python 3.11 or newer
- An OpenAI API key **or** Google Gemini API key

### Steps

```bash
cd enterprise-ai-assistant

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your API key
```

---

## Running Locally

**Terminal 1 — API:**
```bash
make dev
```

**Terminal 2 — Frontend:**
```bash
make frontend-install
make frontend-dev
```

| App | URL |
|-----|-----|
| **Chat UI** | http://127.0.0.1:5173 |
| **Swagger UI** | http://127.0.0.1:8000/docs |
| **API** | http://127.0.0.1:8000 |

---

## Docker (Production)

### Prerequisites

- Docker and Docker Compose
- `.env` file configured with your API key

### Start production stack

```bash
cp .env.example .env
# Edit .env with your API keys

make docker-up
# or
docker compose up -d --build
```

Production endpoints:

| URL | Description |
|-----|-------------|
| http://localhost/ | **Chat UI (main app)** |
| http://localhost/health | Health check |
| http://localhost/docs | Swagger UI |

### Development with Docker (hot reload)

```bash
make docker-dev
# or
docker compose -f docker-compose.dev.yml up --build
```

API available at http://localhost:8000  
Frontend available at http://localhost:5173

### Other Docker commands

```bash
make docker-build    # Build images
make docker-down     # Stop containers
make docker-logs     # Tail logs
make docker-ps       # Show running services
make health          # Ping health endpoint
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | If using OpenAI | — | OpenAI API key |
| `GEMINI_API_KEY` | If using Gemini | — | Google Gemini API key |
| `LLM_PROVIDER` | No | `openai` | `openai` or `gemini` |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |
| `POSTGRES_USER` | No | `assistant` | PostgreSQL username |
| `POSTGRES_PASSWORD` | No | `assistant` | PostgreSQL password |
| `POSTGRES_DB` | No | `enterprise_ai` | PostgreSQL database name |
| `POSTGRES_HOST` | No | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `DATABASE_URL` | No | built from above | Full PostgreSQL connection URL |
| `JWT_SECRET_KEY` | Yes (prod) | — | Secret for signing access tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime |
| `GOOGLE_CLIENT_ID` | For Google login | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | For Google login | — | Google OAuth client secret |
| `GITHUB_CLIENT_ID` | For GitHub login | — | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | For GitHub login | — | GitHub OAuth client secret |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL for OAuth redirects |
| `BACKEND_URL` | No | `http://localhost:8000` | Backend URL for OAuth callbacks |
| `APP_WORKERS` | No | `2` | Uvicorn worker processes |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `NGINX_PORT` | No | `80` | Host port for nginx |
| `API_PORT` | No | `8000` | Host port for dev API |

---

## API Example

```bash
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@company.com","password":"yourpassword"}'

curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"question": "What is the leave policy?"}'
```

### Continue a conversation

```bash
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -H "X-Conversation-Id: <conversation_id_from_previous_response>" \
  -d '{"question": "How many days of annual leave do I get?"}'
```

---

## Sample Responses

### AI Question

```json
{
  "response": "Our leave policy provides employees with paid annual leave...",
  "action": "ai_response",
  "ticket_id": null,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": null
}
```

### Ticket Creation

```json
{
  "response": "Support ticket created successfully.",
  "action": "create_ticket",
  "ticket_id": "INC-1001",
  "conversation_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "Open"
}
```

---

## Engineering Improvements

1. **Multi-turn conversation continuity** — Optional `X-Conversation-Id` header for cross-request memory
2. **Modular package architecture** — Separated core, API, models, and services layers
3. **Production Docker stack** — Multi-stage builds, non-root user, health checks, nginx reverse proxy, PostgreSQL database

---

## License

MIT
