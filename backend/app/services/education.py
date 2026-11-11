"""Education entries: the public list and admin CRUD."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams
from app.core.validators import ensure_date_order
from app.models import Education
from app.repositories.education import EducationRepository
from app.schemas.education import EducationCreate, EducationRead, EducationUpdate
from app.services import crud
from app.services.audit import AuditContext

ENTITY_TYPE = "education"


class EducationNotFoundError(NotFoundError):
    default_message = "Education entry not found"


def _details(education: Education) -> dict[str, object]:
    return {"institution": education.institution, "degree": education.degree}


async def list_education(
    session: AsyncSession, *, q: str | None, page: PageParams
) -> Page[EducationRead]:
    items, total = await EducationRepository(session).search(q=q, page=page)
    return Page.create([EducationRead.model_validate(item) for item in items], total, page)


async def _load(session: AsyncSession, education_id: int) -> Education:
    education = await EducationRepository(session).get(education_id)
    if education is None:
        raise EducationNotFoundError
    return education


async def get_education(session: AsyncSession, education_id: int) -> EducationRead:
    return EducationRead.model_validate(await _load(session, education_id))


async def create_education(
    session: AsyncSession, context: AuditContext, body: EducationCreate
) -> EducationRead:
    ensure_date_order(body.start_date, body.end_date, field="end_date")
    education = Education(**body.model_dump())
    await crud.create(
        session, context, education, entity_type=ENTITY_TYPE, details=_details(education)
    )
    await EducationRepository(session).refresh(education)
    return EducationRead.model_validate(education)


async def update_education(
    session: AsyncSession, context: AuditContext, education_id: int, body: EducationUpdate
) -> EducationRead:
    values = body.model_dump(exclude_unset=True)
    education = await _load(session, education_id)
    # Checked against the stored dates before anything changes.
    sent = body.model_fields_set
    ensure_date_order(
        body.start_date if "start_date" in sent else education.start_date,
        body.end_date if "end_date" in sent else education.end_date,
        field="end_date" if "end_date" in sent else "start_date",
    )
    if await crud.update(session, context, education, values, entity_type=ENTITY_TYPE):
        await EducationRepository(session).refresh(education)
    return EducationRead.model_validate(education)


async def delete_education(session: AsyncSession, context: AuditContext, education_id: int) -> None:
    education = await _load(session, education_id)
    await crud.delete(
        session, context, education, entity_type=ENTITY_TYPE, details=_details(education)
    )
