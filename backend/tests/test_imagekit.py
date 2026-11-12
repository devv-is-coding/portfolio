"""The ImageKit client and helpers, against an in-memory ImageKit (tests/fakes.py)."""

import base64
from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr

from app.core.imagekit import (
    UPLOAD_AUTH_TTL_SECONDS,
    ImageKitClient,
    ImageKitConfig,
    ImageKitNotConfiguredError,
    ImageKitUnavailableError,
    create_http_client,
    create_upload_auth,
    file_url,
    sign_upload,
)
from app.tasks.media import delete_file_from_imagekit
from app.worker import celery_app
from tests.fakes import FakeImageKit, IsolatedSettings

pytestmark = pytest.mark.anyio

CONFIG = ImageKitConfig(
    public_key="public_test",
    private_key="private_test",
    url_endpoint="https://ik.imagekit.io/portfolio",
)


def test_signature_is_hmac_sha1_of_token_and_expire() -> None:
    # The same formula as ImageKit's official SDK (imagekitio 4.x): computed once and
    # pinned here, so any change to the signing breaks this test.
    signature = sign_upload(
        "private_test", token="8f1c6a3e-1b5f-4c51-9d2a-7a3c2e9b4f10", expire=1_800_000_000
    )

    assert signature == "0e0bfd40ee1edee638c80cd2a6966ec7cf545c1b"


def test_upload_auth_expires_after_the_ttl_with_a_fresh_token() -> None:
    first = create_upload_auth("private_test", now=1_000)
    second = create_upload_auth("private_test", now=1_000)

    assert first.expire == 1_000 + UPLOAD_AUTH_TTL_SECONDS
    assert first.token != second.token
    assert first.signature == sign_upload("private_test", token=first.token, expire=first.expire)


@pytest.mark.parametrize(
    ("path", "url"),
    [
        ("/projects/shop.webp", "https://ik.imagekit.io/portfolio/projects/shop.webp"),
        ("projects/shop.webp", "https://ik.imagekit.io/portfolio/projects/shop.webp"),
        ("/a b/ü.png", "https://ik.imagekit.io/portfolio/a%20b/%C3%BC.png"),
    ],
)
def test_file_url(path: str, url: str) -> None:
    assert file_url("https://ik.imagekit.io/portfolio/", path) == url


def test_config_requires_all_settings() -> None:
    with pytest.raises(ImageKitNotConfiguredError):
        ImageKitConfig.from_settings(IsolatedSettings(imagekit_public_key="x"))


def test_config_strips_the_trailing_slash() -> None:
    settings = IsolatedSettings(
        imagekit_public_key="public_test",
        imagekit_private_key=SecretStr("private_test"),
        imagekit_url_endpoint="https://ik.imagekit.io/portfolio/",
    )

    assert ImageKitConfig.from_settings(settings).url_endpoint == CONFIG.url_endpoint


async def test_get_file_details_maps_the_fields_and_authenticates() -> None:
    imagekit = FakeImageKit()
    imagekit.add_file("abc123", "/projects/shop.webp", "image/webp", 2048, 1200, 800)

    async with create_http_client(CONFIG, imagekit.transport) as http:
        details = await ImageKitClient(http).get_file_details("abc123")

    assert details is not None
    assert (details.file_path, details.mime_type, details.size_bytes) == (
        "/projects/shop.webp",
        "image/webp",
        2048,
    )
    assert (details.width, details.height) == (1200, 800)
    expected = base64.b64encode(b"private_test:").decode()
    assert imagekit.authorization_headers == [f"Basic {expected}"]


async def test_documents_have_no_dimensions() -> None:
    imagekit = FakeImageKit()
    imagekit.add_file("pdf1", "/resume.pdf", "application/pdf", 9000, 0, 0)

    async with create_http_client(CONFIG, imagekit.transport) as http:
        details = await ImageKitClient(http).get_file_details("pdf1")

    assert details is not None
    assert (details.width, details.height) == (None, None)


@pytest.mark.parametrize(
    "file_id",
    [
        "6745dd8e432c476416dfe3f0",  # well-formed but unknown: ImageKit answers 404
        "not-a-file-id",  # not an ImageKit id at all: ImageKit answers 400
    ],
)
async def test_unknown_file_is_none(file_id: str) -> None:
    async with create_http_client(CONFIG, FakeImageKit().transport) as http:
        assert await ImageKitClient(http).get_file_details(file_id) is None


async def test_deleting_with_an_invalid_id_is_still_an_upstream_error() -> None:
    """Deletes only use ids ImageKit gave us, so a 400 there is a real failure."""
    imagekit = FakeImageKit()
    imagekit.files["abc"] = {}

    def bad_request(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": "Invalid fileId parameter."})

    async with create_http_client(CONFIG, httpx.MockTransport(bad_request)) as http:
        with pytest.raises(ImageKitUnavailableError):
            await ImageKitClient(http).delete_file("abc")


@pytest.mark.parametrize(
    "handler",
    [
        lambda _request: httpx.Response(500, json={"message": "boom"}),
        lambda _request: httpx.Response(200, json={"unexpected": True}),
        lambda _request: httpx.Response(200, content=b"not json"),
    ],
)
async def test_imagekit_errors_and_bad_responses_are_upstream_errors(
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    transport = httpx.MockTransport(handler)

    async with create_http_client(CONFIG, transport) as http:
        with pytest.raises(ImageKitUnavailableError):
            await ImageKitClient(http).get_file_details("abc123")


async def test_network_failure_is_an_upstream_error() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    async with create_http_client(CONFIG, httpx.MockTransport(fail)) as http:
        with pytest.raises(ImageKitUnavailableError):
            await ImageKitClient(http).delete_file("abc123")


async def test_delete_removes_the_file_and_ignores_missing_ones() -> None:
    imagekit = FakeImageKit()
    imagekit.add_file("abc123", "/a.png", "image/png", 10, 1, 1)

    await delete_file_from_imagekit("abc123", CONFIG, imagekit.transport)
    await delete_file_from_imagekit("abc123", CONFIG, imagekit.transport)  # already gone

    assert imagekit.deleted == ["abc123", "abc123"]
    assert imagekit.files == {}


async def test_file_ids_are_quoted_in_the_url() -> None:
    imagekit = FakeImageKit()

    async with create_http_client(CONFIG, imagekit.transport) as http:
        await ImageKitClient(http).get_file_details("../../files")

    assert imagekit.requested_paths == ["/v1/files/..%2F..%2Ffiles/details"]


def test_delete_task_is_registered_and_retries_imagekit_outages() -> None:
    assert "app.tasks.media" in celery_app.conf.include
    # The finalized task class carries the retry options (`delete_file` itself is a
    # lazy proxy until the Celery app is finalized).
    options = vars(type(celery_app.tasks["media.delete_file"]))
    assert options["autoretry_for"] == (ImageKitUnavailableError,)
    assert options["max_retries"] == 10
    assert options["retry_backoff"] is True
