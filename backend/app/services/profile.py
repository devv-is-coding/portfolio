"""The portfolio owner's profile (exactly one row) and its social links.

The profile always has id 1: the first `PUT` creates it, and the primary key makes a
second profile row impossible.
"""

from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models import Profile, SocialLink
from app.models.enums import MediaKind
from app.repositories.profiles import ProfileRepository
from app.repositories.social_links import SocialLinkRepository
from app.schemas.profile import (
    ProfileRead,
    ProfileUpdate,
    ProfileWrite,
    SocialLinkCreate,
    SocialLinkRead,
    SocialLinkUpdate,
)
from app.services import audit
from app.services.audit import AuditContext
from app.services.media import require_media, to_public

PROFILE_ID = 1
_MEDIA_FIELDS = {"avatar_media_id": MediaKind.IMAGE, "resume_media_id": MediaKind.DOCUMENT}


class ProfileNotFoundError(NotFoundError):
    default_message = "The profile hasn't been created yet"


class SocialLinkNotFoundError(NotFoundError):
    default_message = "Social link not found"


def to_read(profile: Profile, url_endpoint: str | None) -> ProfileRead:
    return ProfileRead(
        full_name=profile.full_name,
        headline=profile.headline,
        biography=profile.biography,
        location=profile.location,
        email=profile.email,
        phone=profile.phone,
        avatar_media_id=profile.avatar_media_id,
        avatar=to_public(profile.avatar, url_endpoint),
        resume_media_id=profile.resume_media_id,
        resume=to_public(profile.resume, url_endpoint),
        social_links=[SocialLinkRead.model_validate(link) for link in profile.social_links],
        updated_at=profile.updated_at,
    )


async def _load(session: AsyncSession) -> Profile:
    profile = await ProfileRepository(session).get_with_details(PROFILE_ID)
    if profile is None:
        raise ProfileNotFoundError
    return profile


async def get_profile(session: AsyncSession, url_endpoint: str | None) -> ProfileRead:
    return to_read(await _load(session), url_endpoint)


async def _check_media(session: AsyncSession, values: Mapping[str, object]) -> None:
    for field, kind in _MEDIA_FIELDS.items():
        media_id = values.get(field)
        if isinstance(media_id, int):
            await require_media(session, media_id, kind, field)


async def replace_profile(
    session: AsyncSession, url_endpoint: str | None, context: AuditContext, body: ProfileWrite
) -> tuple[ProfileRead, bool]:
    """Create the profile, or replace every field of it. Returns (profile, created)."""
    values = body.model_dump(mode="json")
    await _check_media(session, values)
    repo = ProfileRepository(session)
    profile = await repo.get(PROFILE_ID)
    created = profile is None
    if profile is None:
        repo.add(Profile(id=PROFILE_ID, **values))
        audit.record(
            session, context, "profile.create", entity_type="profile", entity_id=PROFILE_ID
        )
    else:
        diff = audit.apply_changes(profile, values)
        if diff:
            audit.record(
                session,
                context,
                "profile.update",
                entity_type="profile",
                entity_id=PROFILE_ID,
                details=diff,
            )
    await session.commit()
    return to_read(await _load(session), url_endpoint), created


async def update_profile(
    session: AsyncSession, url_endpoint: str | None, context: AuditContext, body: ProfileUpdate
) -> ProfileRead:
    values = body.model_dump(mode="json", exclude_unset=True)
    await _check_media(session, values)
    profile = await _load(session)
    diff = audit.apply_changes(profile, values)
    if diff:
        audit.record(
            session,
            context,
            "profile.update",
            entity_type="profile",
            entity_id=PROFILE_ID,
            details=diff,
        )
        await session.commit()
        profile = await _load(session)
    return to_read(profile, url_endpoint)


async def add_social_link(
    session: AsyncSession, context: AuditContext, body: SocialLinkCreate
) -> SocialLinkRead:
    await _load(session)  # 404 until the profile exists
    repo = SocialLinkRepository(session)
    link = SocialLink(profile_id=PROFILE_ID, **body.model_dump(mode="json"))
    repo.add(link)
    await repo.flush()
    audit.record(
        session,
        context,
        "social_link.create",
        entity_type="social_link",
        entity_id=link.id,
        details={"platform": link.platform, "url": link.url},
    )
    await session.commit()
    return SocialLinkRead.model_validate(link)


async def _get_link(session: AsyncSession, link_id: int) -> SocialLink:
    link = await SocialLinkRepository(session).get(link_id)
    if link is None:
        raise SocialLinkNotFoundError
    return link


async def update_social_link(
    session: AsyncSession, context: AuditContext, link_id: int, body: SocialLinkUpdate
) -> SocialLinkRead:
    link = await _get_link(session, link_id)
    diff = audit.apply_changes(link, body.model_dump(mode="json", exclude_unset=True))
    if diff:
        audit.record(
            session,
            context,
            "social_link.update",
            entity_type="social_link",
            entity_id=link.id,
            details=diff,
        )
        await session.commit()
    return SocialLinkRead.model_validate(link)


async def delete_social_link(session: AsyncSession, context: AuditContext, link_id: int) -> None:
    repo = SocialLinkRepository(session)
    link = await _get_link(session, link_id)
    details = {"platform": link.platform, "url": link.url}
    await repo.delete(link)
    audit.record(
        session,
        context,
        "social_link.delete",
        entity_type="social_link",
        entity_id=link_id,
        details=details,
    )
    await session.commit()
