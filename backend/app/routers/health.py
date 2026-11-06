from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionDep
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def check_database(session: SessionDep) -> None:
    """Fail with 503 when MariaDB can't be reached."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc


@router.get(
    "/health",
    dependencies=[Depends(check_database)],
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}},
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
