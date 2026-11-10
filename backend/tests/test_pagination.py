from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.errors import ValidationFailedError, register_exception_handlers
from app.core.pagination import (
    Page,
    PageParams,
    PageParamsDep,
    SearchQuery,
    Sort,
    SortField,
    parse_sort,
    sort_query,
)


def _client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/items")
    async def items(
        page: PageParamsDep,
        sort: Annotated[Sort, Depends(sort_query("title", "published_at", default="title"))],
        q: SearchQuery = None,
    ) -> dict[str, object]:
        return {
            "page": page.page,
            "size": page.size,
            "offset": page.offset,
            "sort": [[field.name, field.descending] for field in sort],
            "q": q,
        }

    return TestClient(app)


def test_defaults() -> None:
    body = _client().get("/items").json()

    assert body == {"page": 1, "size": 20, "offset": 0, "sort": [["title", False]], "q": None}


def test_page_size_sort_and_search_are_parsed() -> None:
    body = (
        _client()
        .get("/items", params={"page": 3, "size": 10, "sort": "-published_at, title", "q": " api "})
        .json()
    )

    assert body["offset"] == 20
    assert body["sort"] == [["published_at", True], ["title", False]]
    assert body["q"] == "api"


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"page": 0}, "query.page"),
        ({"size": 0}, "query.size"),
        ({"size": 101}, "query.size"),
        ({"q": "x" * 101}, "query.q"),
        ({"sort": "password_hash"}, "query.sort"),
        ({"sort": "title,-title"}, "query.sort"),
        ({"sort": ""}, None),  # empty means "use the default": accepted
    ],
)
def test_invalid_parameters_are_422_with_the_field(
    params: dict[str, str | int], field: str | None
) -> None:
    response = _client().get("/items", params=params)

    if field is None:
        assert response.status_code == 200
        return
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert [detail["field"] for detail in error["details"]] == [field]


def test_blank_search_means_no_search() -> None:
    assert _client().get("/items", params={"q": "   "}).json()["q"] is None


def test_unknown_sort_message_lists_the_allowed_fields() -> None:
    with pytest.raises(ValidationFailedError) as raised:
        parse_sort("nope", ("title", "published_at"))

    assert raised.value.details is not None
    assert (
        raised.value.details[0].message == "Invalid sort field 'nope'. Allowed: title, published_at"
    )


def test_invalid_default_fails_when_the_router_is_defined() -> None:
    with pytest.raises(ValidationFailedError):
        sort_query("title", default="-created_at")


def test_parse_sort_keeps_order_and_direction() -> None:
    assert parse_sort("-a,b", ("a", "b")) == (
        SortField(name="a", descending=True),
        SortField(name="b", descending=False),
    )


@pytest.mark.parametrize(("total", "pages"), [(0, 0), (1, 1), (20, 1), (21, 2), (100, 5)])
def test_page_counts_pages(total: int, pages: int) -> None:
    page = Page[str].create(["a"], total, PageParams(page=1, size=20))

    assert page.pages == pages
    assert page.total == total
