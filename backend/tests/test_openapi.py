"""The API documentation stays complete and true to the code (no database needed)."""

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.main import API_VERSION, TAGS, app
from tests.test_route_protection import ADMIN_PREFIX, _routes

BACKEND = Path(__file__).resolve().parents[1]
SPEC: dict[str, Any] = app.openapi()
OPERATIONS = [
    (f"{method.upper()} {path}", operation)
    for path, item in SPEC["paths"].items()
    for method, operation in item.items()
]
# The only token-protected route outside /admin: the current admin's own account.
TOKEN_ROUTES_OUTSIDE_ADMIN = {"/auth/me"}
# Read by uvicorn (`fastapi run`), not by the app's Settings.
SERVER_VARIABLES = {"FORWARDED_ALLOW_IPS", "WEB_CONCURRENCY"}
# The main create bodies carry a full request example for Swagger's "Try it out".
BODIES_WITH_EXAMPLES = {
    "LoginRequest",
    "ProfileWrite",
    "SocialLinkCreate",
    "SkillCreate",
    "ProjectCreate",
    "ExperienceCreate",
    "EducationCreate",
    "CertificationCreate",
    "BlogTermCreate",
    "BlogPostCreate",
    "ContactMessageCreate",
}


def test_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))

    assert SPEC["info"]["version"] == API_VERSION == pyproject["project"]["version"]
    assert SPEC["info"]["description"].strip()


def test_every_tag_is_described_and_used() -> None:
    used = {tag for _, operation in OPERATIONS for tag in operation["tags"]}

    assert {tag["name"] for tag in TAGS} == used
    assert all(tag["description"].strip() for tag in TAGS)


@pytest.mark.parametrize(("name", "operation"), OPERATIONS, ids=[name for name, _ in OPERATIONS])
def test_every_operation_has_a_summary_description_and_tag(
    name: str, operation: dict[str, Any]
) -> None:
    assert operation.get("summary"), name
    assert operation.get("description", "").strip(), f"{name}: add a docstring"
    assert operation.get("tags"), name


@pytest.mark.parametrize(("name", "operation"), OPERATIONS, ids=[name for name, _ in OPERATIONS])
def test_bearer_auth_and_errors_are_documented(name: str, operation: dict[str, Any]) -> None:
    path = name.split(" ", 1)[1]
    needs_token = path.startswith(ADMIN_PREFIX) or path in TOKEN_ROUTES_OUTSIDE_ADMIN
    responses = operation["responses"]

    assert (operation.get("security") == [{"HTTPBearer": []}]) is needs_token, name
    if needs_token:
        assert "401" in responses, name
    if operation.get("parameters") or operation.get("requestBody"):
        assert "422" in responses, name


def _body_models() -> dict[str, type[BaseModel]]:
    models: dict[str, type[BaseModel]] = {}
    for route in _routes(app):
        for param in route.dependant.body_params:
            model = param.field_info.annotation
            if isinstance(model, type) and issubclass(model, BaseModel):
                models[model.__name__] = model
    return models


def test_main_bodies_have_examples_that_pass_their_own_validation() -> None:
    models = _body_models()
    with_examples = {
        name: model.model_config.get("json_schema_extra")
        for name, model in models.items()
        if model.model_config.get("json_schema_extra")
    }

    assert set(with_examples) == BODIES_WITH_EXAMPLES
    for name, extra in with_examples.items():
        assert isinstance(extra, dict)
        examples = extra["examples"]
        assert isinstance(examples, list) and examples, name
        for example in examples:
            models[name].model_validate(example)  # raises if the example is out of date


def test_env_example_lists_every_setting() -> None:
    text = (BACKEND / ".env.example").read_text(encoding="utf-8")
    documented = set(re.findall(r"^#? ?([A-Z][A-Z0-9_]+)=", text, re.MULTILINE))
    settings = {name.upper() for name in Settings.model_fields}

    assert settings - documented == set(), "add these to .env.example"
    assert documented - settings == SERVER_VARIABLES, "unknown variables in .env.example"
