from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response, status

from app.core.config import SettingsDep
from app.core.database import SessionDep
from app.core.email import ContactNotification, SmtpConfig
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.core.redis import RedisDep
from app.dependencies import AuditContextDep, ClientIpDep, get_current_user
from app.models.enums import ContactMessageStatus
from app.schemas.contact import ContactMessageCreate, ContactMessageRead, ContactMessageUpdate
from app.services import contact as contact_service
from app.services.rate_limit import contact_rate_limiter
from app.tasks.contact import enqueue_notification, notify_admin_in_api

router = APIRouter(prefix="/contact", tags=["contact"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/contact-messages",
    tags=["contact"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

MessageId = Annotated[int, Path(ge=1)]
MessageSort = Annotated[Sort, Depends(sort_query("created_at", "name", default="-created_at"))]


def get_notifier(
    settings: SettingsDep, background: BackgroundTasks
) -> contact_service.Notifier | None:
    """Emails the site owner after the response when SMTP is configured: queued for the
    Celery worker, or sent by the API itself with TASK_RUNNER=api. Overridden in tests."""
    config = SmtpConfig.from_settings(settings)
    if config is None:
        return None
    if settings.task_runner == "celery":
        return enqueue_notification

    def notify_in_api(notification: ContactNotification) -> None:
        background.add_task(notify_admin_in_api, notification, config)

    return notify_in_api


NotifierDep = Annotated[contact_service.Notifier | None, Depends(get_notifier)]


@router.post("", status_code=status.HTTP_202_ACCEPTED, responses=error_responses(429))
async def send_message(
    body: ContactMessageCreate,
    client_ip: ClientIpDep,
    session: SessionDep,
    redis: RedisDep,
    settings: SettingsDep,
    notify: NotifierDep,
) -> Response:
    """Send a message to the site owner. Answers 202 with no body; after too many
    messages from one IP, 429 with `Retry-After`."""
    limiter = contact_rate_limiter(redis, settings)
    await contact_service.submit(session, limiter, notify, client_ip, body)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@admin_router.get("")
async def list_messages(
    session: SessionDep,
    page: PageParamsDep,
    sort: MessageSort,
    q: SearchQuery = None,
    message_status: Annotated[
        ContactMessageStatus | None, Query(alias="status", description="Only this status.")
    ] = None,
) -> Page[ContactMessageRead]:
    """The inbox, newest first. `q` searches the sender's name and email and the subject."""
    return await contact_service.list_messages(
        session, status=message_status, q=q, sort=sort, page=page
    )


@admin_router.get("/{message_id}", responses=error_responses(404))
async def get_message(message_id: MessageId, session: SessionDep) -> ContactMessageRead:
    """One message with the sender's details and IP."""
    return await contact_service.get_message(session, message_id)


@admin_router.patch("/{message_id}", responses=error_responses(404))
async def update_message(
    message_id: MessageId,
    body: ContactMessageUpdate,
    context: AuditContextDep,
    session: SessionDep,
) -> ContactMessageRead:
    """Mark the message read, replied or archived (or unread again)."""
    return await contact_service.update_message(session, context, message_id, body)


@admin_router.delete(
    "/{message_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_message(
    message_id: MessageId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Delete the message for good; the audit entry keeps only its id."""
    await contact_service.delete_message(session, context, message_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
