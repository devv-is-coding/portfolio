"""Work experience: the public timeline and admin CRUD."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams
from app.core.validators import ensure_date_order
from app.models import Experience
from app.repositories.experiences import ExperienceRepository
from app.schemas.experience import ExperienceCreate, ExperienceRead, ExperienceUpdate
from app.services import crud
from app.services.audit import AuditContext

ENTITY_TYPE = "experience"


class ExperienceNotFoundError(NotFoundError):
    default_message = "Experience not found"


def _details(experience: Experience) -> dict[str, object]:
    return {"company": experience.company, "position": experience.position}


async def list_experiences(
    session: AsyncSession, *, q: str | None, page: PageParams
) -> Page[ExperienceRead]:
    items, total = await ExperienceRepository(session).search(q=q, page=page)
    return Page.create([ExperienceRead.model_validate(item) for item in items], total, page)


async def _load(session: AsyncSession, experience_id: int) -> Experience:
    experience = await ExperienceRepository(session).get(experience_id)
    if experience is None:
        raise ExperienceNotFoundError
    return experience


async def get_experience(session: AsyncSession, experience_id: int) -> ExperienceRead:
    return ExperienceRead.model_validate(await _load(session, experience_id))


async def create_experience(
    session: AsyncSession, context: AuditContext, body: ExperienceCreate
) -> ExperienceRead:
    ensure_date_order(body.start_date, body.end_date, field="end_date")
    experience = Experience(**body.model_dump())
    await crud.create(
        session, context, experience, entity_type=ENTITY_TYPE, details=_details(experience)
    )
    await ExperienceRepository(session).refresh(experience)
    return ExperienceRead.model_validate(experience)


async def update_experience(
    session: AsyncSession, context: AuditContext, experience_id: int, body: ExperienceUpdate
) -> ExperienceRead:
    values = body.model_dump(exclude_unset=True)
    experience = await _load(session, experience_id)
    # Checked against the stored dates before anything changes.
    sent = body.model_fields_set
    ensure_date_order(
        body.start_date if "start_date" in sent else experience.start_date,
        body.end_date if "end_date" in sent else experience.end_date,
        field="end_date" if "end_date" in sent else "start_date",
    )
    if await crud.update(session, context, experience, values, entity_type=ENTITY_TYPE):
        await ExperienceRepository(session).refresh(experience)
    return ExperienceRead.model_validate(experience)


async def delete_experience(
    session: AsyncSession, context: AuditContext, experience_id: int
) -> None:
    experience = await _load(session, experience_id)
    await crud.delete(
        session, context, experience, entity_type=ENTITY_TYPE, details=_details(experience)
    )
