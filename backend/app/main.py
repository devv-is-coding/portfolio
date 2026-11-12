from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import register_exception_handlers
from app.core.http_cache import HttpCacheMiddleware
from app.core.http_security import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.core.logging import RequestContextMiddleware, configure_logging
from app.core.redis import redis_client
from app.core.sentry import init_sentry
from app.routers import (
    audit_logs,
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


# Keep in step with `version` in pyproject.toml (tests/test_openapi.py checks it).
API_VERSION = "0.1.0"

API_DESCRIPTION = """
The backend of the portfolio site: public reads for the pages, admin routes to manage
the content.

- **Public routes** (`/projects`, `/blog/posts`, ...) return published content only and
  need no token. They send an `ETag`; repeat the request with `If-None-Match` to get a
  `304 Not Modified` when nothing changed.
- **Admin routes** (`/admin/...`) need `Authorization: Bearer <access token>` from
  `POST /auth/login` (15 minutes; renew it with `POST /auth/refresh`). Every change is
  written to the audit log.
- **Errors** always look like `{"error": {"code", "message", "details"}}`; validation
  errors list the fields in `details`, never the values sent.
- **Lists** take `page` (from 1), `size` (1-100, default 20) and, where offered,
  `sort` (e.g. `-published_at`) and `q` (search); they return
  `{"items", "total", "page", "size", "pages"}`.
"""

TAGS = [
    {"name": "health", "description": "Is the API up and can it reach the database?"},
    {"name": "auth", "description": "Admin login, token refresh and logout."},
    {
        "name": "media",
        "description": "Images and PDFs in ImageKit: signed browser uploads, then registered here.",
    },
    {"name": "profile", "description": "The site owner's profile (one) and social links."},
    {"name": "skills", "description": "Skills shown on the site and linked to projects."},
    {
        "name": "projects",
        "description": "Projects with a gallery and skills; drafts and archived ones stay private.",
    },
    {"name": "experience", "description": "Work history, current jobs first."},
    {"name": "education", "description": "Schools and degrees."},
    {
        "name": "certifications",
        "description": "Certifications; expired ones are flagged, not hidden.",
    },
    {"name": "blog", "description": "Markdown posts, categories and tags."},
    {
        "name": "contact",
        "description": "The public contact form (rate-limited) and the admin inbox.",
    },
    {
        "name": "settings",
        "description": "Site settings as JSON values; only `site.*` and `seo.*` keys are public.",
    },
    {"name": "audit", "description": "Read-only history of every admin change and security event."},
]

app = FastAPI(
    title=settings.app_name,
    version=API_VERSION,
    description=API_DESCRIPTION,
    openapi_tags=TAGS,
    lifespan=lifespan,
)
register_exception_handlers(app)

# Inside CORS, so even a 413 or a 304 carries the CORS headers the browser needs.
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
app.add_middleware(HttpCacheMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Lets the browser read the request id, e.g. to show it next to an error.
    expose_headers=["X-Request-ID"],
)
# JSON compresses well (a blog post is up to 200,000 characters); small bodies aren't worth it.
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment == "production")
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
app.include_router(audit_logs.admin_router)
