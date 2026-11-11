from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import register_exception_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.core.redis import redis_client
from app.core.sentry import init_sentry
from app.routers import (
    auth,
    blog,
    certifications,
    contact,
    education,
    experiences,
    health,
    media,
    profile,
    projects,
    site_settings,
    skills,
)

settings = get_settings()
configure_logging(settings)
init_sentry(settings)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    # Close pooled MariaDB and Redis connections on shutdown.
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Lets the browser read the request id, e.g. to show it next to an error.
    expose_headers=["X-Request-ID"],
)
# Added last, so it's the outermost middleware: every response (CORS preflights and
# errors included) gets a request id and an access log line.
app.add_middleware(RequestContextMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(media.router)
app.include_router(profile.router)
app.include_router(profile.admin_router)
app.include_router(skills.router)
app.include_router(skills.admin_router)
app.include_router(projects.router)
app.include_router(projects.admin_router)
app.include_router(experiences.router)
app.include_router(experiences.admin_router)
app.include_router(education.router)
app.include_router(education.admin_router)
app.include_router(certifications.router)
app.include_router(certifications.admin_router)
app.include_router(blog.router)
app.include_router(blog.admin_router)
app.include_router(contact.router)
app.include_router(contact.admin_router)
app.include_router(site_settings.router)
app.include_router(site_settings.admin_router)
