"""Tests for pilot allowlist access and required configuration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.access import is_allowed_email, load_allowed_testers, normalize_email
from app.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_email_normalization_is_case_and_whitespace_insensitive() -> None:
    """Approved identifiers should work despite normal user input variation."""
    testers = load_allowed_testers(ROOT / "config/allowed-testers.json")

    assert normalize_email("  GCARLETTO@WORLDBANK.ORG ") == "gcarletto@worldbank.org"
    assert is_allowed_email("  GCARLETTO@WORLDBANK.ORG ", testers) is True
    assert is_allowed_email("other@example.org", testers) is False


@pytest.mark.parametrize(
    "email",
    [
        "gcarletto@worldbank.org",
        "asolatorio@worldbank.org",
        "zprinsloo@worldbank.org",
        "userajuddin@worldbank.org",
        "dmahler@worldbank.org",
        "hdang@worldbank.org",
    ],
)
def test_every_approved_email_is_allowed(email: str) -> None:
    """The configured six-person pilot allowlist is complete."""
    testers = load_allowed_testers(ROOT / "config/allowed-testers.json")

    assert is_allowed_email(email, testers) is True


def test_settings_require_session_secret_and_response_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime settings must not silently invent security or storage values."""
    monkeypatch.delenv("APP_SESSION_SECRET", raising=False)
    monkeypatch.delenv("RESPONSE_PATH", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
