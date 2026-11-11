"""The public contact form (rate-limited, with a spam trap) and the admin inbox."""

import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import ContactNotification
from app.core.errors import NotFoundError, RateLimitedError
from app.core.pagination import Page, PageParams, Sort
from app.models import ContactMessage
from app.models.enums import ContactMessageStatus
from app.repositories.contact_messages import ContactMessageRepository
from app.schemas.contact import ContactMessageCreate, ContactMessageRead, ContactMessageUpdate
from app.services import crud
from app.services.audit import AuditContext
from app.services.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

ENTITY_TYPE = "contact_message"

type Notifier = Callable[[ContactNotification], None]


class ContactMessageNotFoundError(NotFoundError):
    default_message = "Message not found"


async def submit(
    session: AsyncSession,
    limiter: RateLimiter,
    notify: Notifier | None,
    client_ip: str | None,
    body: ContactMessageCreate,
) -> None:
    """Store the message and queue the email (when SMTP is configured).

    Every submission counts against the per-IP limit, spam included. A filled spam
    trap gets the same answer as a real message, so bots learn nothing, but nothing
    is stored or sent.
    """
    limiter_key = client_ip or "unknown"
    retry_after = await limiter.retry_after(limiter_key)
    if retry_after is not None:
        raise RateLimitedError("Too many messages, try again later", retry_after=retry_after)
    await limiter.hit(limiter_key)
    if body.website:
        logger.info("Contact message dropped: spam trap filled")
        return
    message = ContactMessage(
        **body.model_dump(exclude={"website"}),
        ip_address=client_ip,
    )
    ContactMessageRepository(session).add(message)
    await session.commit()
    if notify is not None:
        notify(
            ContactNotification(
                message_id=message.id,
                name=message.name,
                email=message.email,
                subject=message.subject,
                message=message.message,
            )
        )


async def list_messages(
    session: AsyncSession,
    *,
    status: ContactMessageStatus | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[ContactMessageRead]:
    items, total = await ContactMessageRepository(session).search(
        status=status, q=q, sort=sort, page=page
    )
    return Page.create([ContactMessageRead.model_validate(item) for item in items], total, page)


async def _load(session: AsyncSession, message_id: int) -> ContactMessage:
    message = await ContactMessageRepository(session).get(message_id)
    if message is None:
        raise ContactMessageNotFoundError
    return message


async def get_message(session: AsyncSession, message_id: int) -> ContactMessageRead:
    return ContactMessageRead.model_validate(await _load(session, message_id))


async def update_message(
    session: AsyncSession, context: AuditContext, message_id: int, body: ContactMessageUpdate
) -> ContactMessageRead:
    """Change the status (unread, read, replied, archived)."""
    message = await _load(session, message_id)
    values = body.model_dump(exclude_unset=True)
    if await crud.update(session, context, message, values, entity_type=ENTITY_TYPE):
        await ContactMessageRepository(session).refresh(message)
    return ContactMessageRead.model_validate(message)


async def delete_message(session: AsyncSession, context: AuditContext, message_id: int) -> None:
    """Gone for good. The audit entry keeps only the id, not the sender's details."""
    message = await _load(session, message_id)
    await crud.delete(session, context, message, entity_type=ENTITY_TYPE)
