"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.api.router import api_router
from app.core.config import CORS_ORIGINS
from app.core.logging import setup_logging
from app.core.openapi_custom import SWAGGER_UI_HIDE_MEDIA_TYPE_CSS, simplify_openapi_schema
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
        docs_url=None,
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

    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema
        openapi_schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
            tags=OPENAPI_TAGS,
        )
        application.openapi_schema = simplify_openapi_schema(openapi_schema)
        return application.openapi_schema

    application.openapi = custom_openapi

    @application.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        """Swagger UI with media-type controls hidden and examples emphasized."""
        html = get_swagger_ui_html(
            openapi_url=application.openapi_url,
            title=f"{application.title} - Swagger UI",
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
                "defaultModelExpandDepth": -1,
                "docExpansion": "list",
                "tryItOutEnabled": True,
                "displayRequestDuration": True,
            },
        )
        body = html.body.decode("utf-8").replace("</head>", f"{SWAGGER_UI_HIDE_MEDIA_TYPE_CSS}</head>")
        return HTMLResponse(content=body)

    return application


app = create_app()
