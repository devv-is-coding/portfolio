"""Every admin route requires a logged-in admin.

The checks walk `app.routes`, so routes added later are covered automatically:
an `/admin` route without `get_current_user` (directly, through `CurrentUserDep`,
`AuditContextDep` or a router-level dependency) fails this file.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient

from app.dependencies import CurrentUserDep, get_current_user
from app.main import app

ADMIN_PREFIX = "/admin"


def _depends_on(dependant: Dependant, call: Callable[..., Any]) -> bool:
    return any(sub.call is call or _depends_on(sub, call) for sub in dependant.dependencies)


@dataclass(frozen=True)
class _Route:
    path: str
    methods: frozenset[str]
    dependant: Dependant


def _routes(application: FastAPI) -> list[_Route]:
    """The effective API routes, prefixes and router-level dependencies included.

    FastAPI includes routers lazily, so `app.routes` holds wrappers;
    `iter_route_contexts` (what FastAPI's OpenAPI generation uses) resolves them.
    """
    routes = []
    for context in iter_route_contexts(application.routes):
        dependant = getattr(context, "dependant", None)
        if context.path and isinstance(dependant, Dependant):
            routes.append(_Route(context.path, frozenset(context.methods or ()), dependant))
    return routes


def unprotected_admin_routes(application: FastAPI) -> list[str]:
    return [
        route.path
        for route in _routes(application)
        if route.path.startswith(ADMIN_PREFIX)
        and not _depends_on(route.dependant, get_current_user)
    ]


def _protected_requests() -> list[tuple[str, str]]:
    """(method, concrete path) for every route that needs the current user."""
    return [
        (method, re.sub(r"\{[^}]+\}", "1", route.path))
        for route in _routes(app)
        if _depends_on(route.dependant, get_current_user)
        for method in sorted(route.methods)
    ]


def test_every_admin_route_requires_the_current_user() -> None:
    assert unprotected_admin_routes(app) == []


def test_the_check_catches_an_unprotected_admin_route() -> None:
    application = FastAPI()

    @application.get("/admin/leak")
    async def leak() -> None:
        return None

    @application.get("/admin/safe")
    async def safe(_user: CurrentUserDep) -> None:
        return None

    protected_router = APIRouter(prefix="/admin/items", dependencies=[Depends(get_current_user)])

    @protected_router.get("")
    async def items() -> None:
        return None

    open_router = APIRouter(prefix="/admin/open")

    @open_router.get("")
    async def open_items() -> None:
        return None

    application.include_router(protected_router)
    application.include_router(open_router)

    assert sorted(unprotected_admin_routes(application)) == ["/admin/leak", "/admin/open"]


def test_protected_routes_are_found() -> None:
    assert ("GET", "/auth/me") in _protected_requests()


@pytest.mark.parametrize(("method", "path"), _protected_requests())
def test_protected_route_rejects_requests_without_a_token(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


# The only routes outside /admin that change anything: auth and the contact form.
PUBLIC_WRITES = {
    ("POST", "/auth/login"),
    ("POST", "/auth/refresh"),
    ("POST", "/auth/logout"),
    ("POST", "/contact"),
}


def test_public_routes_only_read_except_auth_and_contact() -> None:
    writes = {
        (method, route.path)
        for route in _routes(app)
        if not route.path.startswith(ADMIN_PREFIX)
        for method in route.methods - {"GET", "HEAD"}
    }

    assert writes == PUBLIC_WRITES


def test_every_request_body_rejects_unknown_fields() -> None:
    """No mass assignment: a field the schema doesn't declare is a 422, never ignored."""
    lenient = sorted(
        f"{route.path}: {param.field_info.annotation}"
        for route in _routes(app)
        for param in route.dependant.body_params
        if getattr(param.field_info.annotation, "model_config", {}).get("extra") != "forbid"
    )

    assert lenient == []
