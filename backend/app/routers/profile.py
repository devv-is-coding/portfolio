from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.imagekit import MediaUrlEndpointDep
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.profile import (
    ProfileRead,
    ProfileUpdate,
    ProfileWrite,
    SocialLinkCreate,
    SocialLinkRead,
    SocialLinkUpdate,
)
from app.services import profile as profile_service

router = APIRouter(prefix="/profile", tags=["profile"])
admin_router = APIRouter(
    prefix="/admin/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422),
)

LinkId = Annotated[int, Path(ge=1)]


@router.get("", responses=error_responses(404, 503))
async def get_profile(session: SessionDep, url_endpoint: MediaUrlEndpointDep) -> ProfileRead:
    """The portfolio owner's public profile with avatar, resume and social links.

    404 until the admin creates it with `PUT /admin/profile`.
    """
    return await profile_service.get_profile(session, url_endpoint)


@admin_router.put("", responses={201: {"description": "Profile created"}, **error_responses(503)})
async def replace_profile(
    body: ProfileWrite,
    response: Response,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProfileRead:
    """Create the profile (201) or replace all of it (200). Fields left out become empty.

    The avatar must be an image and the resume a PDF from the media library.
    """
    profile, created = await profile_service.replace_profile(session, url_endpoint, context, body)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return profile


@admin_router.patch("", responses=error_responses(404, 503))
async def update_profile(
    body: ProfileUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProfileRead:
    """Change only the fields sent; `null` clears an optional field."""
    return await profile_service.update_profile(session, url_endpoint, context, body)


@admin_router.post(
    "/social-links", status_code=status.HTTP_201_CREATED, responses=error_responses(404)
)
async def add_social_link(
    body: SocialLinkCreate, context: AuditContextDep, session: SessionDep
) -> SocialLinkRead:
    """Add a social link (http/https URL). The profile must exist."""
    return await profile_service.add_social_link(session, context, body)


@admin_router.patch("/social-links/{link_id}", responses=error_responses(404))
async def update_social_link(
    link_id: LinkId, body: SocialLinkUpdate, context: AuditContextDep, session: SessionDep
) -> SocialLinkRead:
    """Change only the fields sent (platform, URL, display order)."""
    return await profile_service.update_social_link(session, context, link_id, body)


@admin_router.delete(
    "/social-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404),
)
async def delete_social_link(
    link_id: LinkId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Remove the link from the profile."""
    await profile_service.delete_social_link(session, context, link_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
