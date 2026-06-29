"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.router import api_router
from app.core.config import CORS_ORIGINS
from app.core.logging import setup_logging
from app.db.session import init_db
from app.models.openapi import OPENAPI_DESCRIPTION, OPENAPI_TAGS


@asynccontextmanager
async def lifespan(_application: FastAPI):
    """Initialize resources on startup."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    application = FastAPI(
        title="Enterprise AI Assistant",
        description=OPENAPI_DESCRIPTION,
        version=__version__,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        contact={
            "name": "Enterprise AI Assistant",
            "url": "https://github.com/enterprise-ai-assistant",
        },
        license_info={"name": "MIT"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return clear validation errors for invalid question payloads."""
        errors = exc.errors()
        messages = []

        for error in errors:
            if error.get("loc")[-1] == "question":
                message = error.get("msg", "Invalid question.")
                if message.startswith("Value error, "):
                    message = message.replace("Value error, ", "", 1)
                messages.append(message)

        detail = messages[0] if messages else "Invalid request payload."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": detail},
        )

    application.include_router(api_router)
    return application


app = create_app()
