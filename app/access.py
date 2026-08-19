"""Approved tester allowlist and session identity helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AccessConfigError(ValueError):
    """Raised when the approved tester configuration is invalid."""


def normalize_email(email: str) -> str:
    """Normalize an email identifier for allowlist comparison.

    Args:
        email: User-entered email identifier.

    Returns:
        Trimmed, case-folded email string.

    Example:
        >>> normalize_email(" GCARLETTO@WORLDBANK.ORG ")
        'gcarletto@worldbank.org'
    """
    if not isinstance(email, str):
        raise TypeError("email must be a string")
    return email.strip().casefold()


def load_allowed_testers(path: Path) -> dict[str, dict[str, str]]:
    """Load the configured approved tester identities.

    Args:
        path: JSON configuration path.

    Returns:
        Mapping of normalized email to display metadata.

    Raises:
        AccessConfigError: If the file is missing, malformed, or duplicated.

    Example:
        >>> testers = load_allowed_testers(Path("config/allowed-testers.json"))
        >>> testers["gcarletto@worldbank.org"]["name"]
        'Gero Carletto'
    """
    try:
        raw_config: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise AccessConfigError(f"Allowed tester file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise AccessConfigError(
            f"Allowed tester file is invalid JSON: {path}"
        ) from error

    raw_testers = raw_config.get("testers") if isinstance(raw_config, dict) else None
    if not isinstance(raw_testers, list) or not raw_testers:
        raise AccessConfigError(
            "Allowed tester config must contain a non-empty testers list"
        )

    testers: dict[str, dict[str, str]] = {}
    for raw_tester in raw_testers:
        if not isinstance(raw_tester, dict) or not isinstance(
            raw_tester.get("email"), str
        ):
            raise AccessConfigError("Every allowed tester must contain an email")
        email = normalize_email(raw_tester["email"])
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise AccessConfigError(f"Invalid allowed tester email: {email}")
        if email in testers:
            raise AccessConfigError(f"Duplicate allowed tester email: {email}")
        name = raw_tester.get("name", "")
        if not isinstance(name, str):
            raise AccessConfigError(f"Tester name must be text: {email}")
        testers[email] = {"email": email, "name": name.strip()}
    return testers


def is_allowed_email(email: str, testers: dict[str, dict[str, str]]) -> bool:
    """Return whether an email identifier is in the normalized allowlist.

    Args:
        email: User-entered email identifier.
        testers: Mapping returned by :func:`load_allowed_testers`.

    Returns:
        ``True`` for an approved identifier and ``False`` otherwise.

    Example:
        >>> is_allowed_email("gcarletto@worldbank.org", testers)
        True
    """
    return normalize_email(email) in testers
