from app.services.audit import REDACTED, redact


def test_redacts_sensitive_keys_at_any_depth_and_case() -> None:
    details = {
        "title": {"old": "A", "new": "B"},
        "Password": "hunter2",
        "nested": {"refresh_token": "abc", "items": [{"token_hash": "x", "keep": 1}]},
    }

    assert redact(details) == {
        "title": {"old": "A", "new": "B"},
        "Password": REDACTED,
        "nested": {"refresh_token": REDACTED, "items": [{"token_hash": REDACTED, "keep": 1}]},
    }


def test_does_not_modify_the_input() -> None:
    details = {"password": "hunter2"}

    redact(details)

    assert details == {"password": "hunter2"}
