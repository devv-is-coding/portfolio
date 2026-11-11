"""Publication rules shared by projects and blog posts."""

from datetime import datetime

from app.core.errors import ValidationFailedError
from app.core.security import utc_now
from app.models import BlogPost, Project
from app.models.enums import PublicationStatus
from app.schemas.errors import ErrorDetail


def resolve_published_at(
    status: PublicationStatus, published_at: datetime | None, *, sent: bool
) -> datetime | None:
    """The `published_at` to store, checked before anything is changed.

    A published row needs `published_at` (the database checks it): when the request
    didn't send one, it becomes now; an explicit `null` while published is a 422.
    """
    if status is not PublicationStatus.PUBLISHED or published_at is not None:
        return published_at
    if sent:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field="body.published_at",
                    message="Required while the status is published",
                    type="published_at_required",
                )
            ]
        )
    return utc_now()


def publication_values(
    instance: Project | BlogPost,
    status: PublicationStatus | None,
    published_at: datetime | None,
    sent: set[str],
) -> dict[str, object]:
    """`status` and `published_at` for a PATCH: the sent values merged with the stored
    ones, checked before the instance changes (so a 422 leaves it untouched)."""
    new_status = status if status is not None and "status" in sent else instance.status
    return {
        "status": new_status,
        "published_at": resolve_published_at(
            new_status,
            published_at if "published_at" in sent else instance.published_at,
            sent="published_at" in sent,
        ),
    }
