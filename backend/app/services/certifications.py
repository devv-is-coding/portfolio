"""Certifications: the public list (expired ones flagged, not hidden) and admin CRUD, with an
optional picture of each certificate from the media library."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams
from app.core.validators import ensure_date_order
from app.models import Certification
from app.models.enums import MediaKind
from app.repositories.certifications import CertificationRepository
from app.schemas.certification import CertificationCreate, CertificationRead, CertificationUpdate
from app.services import crud
from app.services.audit import AuditContext
from app.services.media import require_media, to_public

ENTITY_TYPE = "certification"
EXPIRY_MESSAGE = "Must not be before the issue date"


class CertificationNotFoundError(NotFoundError):
    default_message = "Certification not found"


def to_read(certification: Certification, url_endpoint: str | None) -> CertificationRead:
    return CertificationRead(
        id=certification.id,
        name=certification.name,
        issuing_organization=certification.issuing_organization,
        credential_id=certification.credential_id,
        credential_url=certification.credential_url,
        issued_at=certification.issued_at,
        expires_at=certification.expires_at,
        image_media_id=certification.image_media_id,
        image=to_public(certification.image, url_endpoint),
        created_at=certification.created_at,
        updated_at=certification.updated_at,
    )


def _details(certification: Certification) -> dict[str, object]:
    return {
        "name": certification.name,
        "issuing_organization": certification.issuing_organization,
    }


def _column_values(body: CertificationCreate | CertificationUpdate) -> dict[str, object]:
    """The fields sent, with the URL as the string the column stores."""
    values = body.model_dump(exclude_unset=True)
    if values.get("credential_url") is not None:
        values["credential_url"] = str(values["credential_url"])
    return values


async def _require_image(session: AsyncSession, image_media_id: int | None) -> None:
    if image_media_id is not None:
        await require_media(session, image_media_id, MediaKind.IMAGE, "image_media_id")


async def list_certifications(
    session: AsyncSession, url_endpoint: str | None, *, q: str | None, page: PageParams
) -> Page[CertificationRead]:
    items, total = await CertificationRepository(session).search(q=q, page=page)
    return Page.create([to_read(item, url_endpoint) for item in items], total, page)


async def _load(session: AsyncSession, certification_id: int) -> Certification:
    certification = await CertificationRepository(session).get_with_image(certification_id)
    if certification is None:
        raise CertificationNotFoundError
    return certification


async def get_certification(
    session: AsyncSession, url_endpoint: str | None, certification_id: int
) -> CertificationRead:
    return to_read(await _load(session, certification_id), url_endpoint)


async def create_certification(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    body: CertificationCreate,
) -> CertificationRead:
    ensure_date_order(body.issued_at, body.expires_at, field="expires_at", message=EXPIRY_MESSAGE)
    await _require_image(session, body.image_media_id)
    certification = Certification(**_column_values(body))
    await crud.create(
        session, context, certification, entity_type=ENTITY_TYPE, details=_details(certification)
    )
    return to_read(await _load(session, certification.id), url_endpoint)


async def update_certification(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    certification_id: int,
    body: CertificationUpdate,
) -> CertificationRead:
    values = _column_values(body)
    certification = await _load(session, certification_id)
    # Checked against the stored dates before anything changes.
    sent = body.model_fields_set
    ensure_date_order(
        body.issued_at if "issued_at" in sent else certification.issued_at,
        body.expires_at if "expires_at" in sent else certification.expires_at,
        field="expires_at" if "expires_at" in sent else "issued_at",
        message=EXPIRY_MESSAGE,
    )
    await _require_image(session, body.image_media_id)
    if await crud.update(session, context, certification, values, entity_type=ENTITY_TYPE):
        certification = await _load(session, certification_id)
    return to_read(certification, url_endpoint)


async def delete_certification(
    session: AsyncSession, context: AuditContext, certification_id: int
) -> None:
    certification = await _load(session, certification_id)
    await crud.delete(
        session, context, certification, entity_type=ENTITY_TYPE, details=_details(certification)
    )
