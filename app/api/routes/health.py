"""Health check route."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.session import check_database
from app.models.openapi import HEALTH_RESPONSES
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the current health status of the API and database connectivity.",
    responses=HEALTH_RESPONSES,
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """Simple health check endpoint."""
    db_ok = check_database()
    payload = HealthResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "unavailable",
    )

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload.model_dump(),
        )

    return payload
