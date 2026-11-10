from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionDep, ping
from app.core.errors import ServiceUnavailableError, error_responses
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def check_database(session: SessionDep) -> None:
    """Fail with 503 when MariaDB can't be reached."""
    try:
        await ping(session)
    except SQLAlchemyError as exc:
        raise ServiceUnavailableError("Database unavailable") from exc


@router.get(
    "/health",
    dependencies=[Depends(check_database)],
    responses=error_responses(503),
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
