"""Load and validate the normalized survey review manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_REVIEW_POINT_IDS = (
    "G1",
    "G2",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "Q5",
    "Q6",
    "Q7",
    "product-reference",
    "Q8",
    "Q9",
    "Q10",
    "Q11",
    "Q12",
    "optional-evidence",
)
JUDGMENT_OPTIONS = ("Good question", "Bad question", "Needs refinement")


class ManifestError(ValueError):
    """Raised when the review manifest is missing or structurally invalid."""


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and validate a survey manifest from JSON.

    Args:
        path: JSON manifest path.

    Returns:
        A validated manifest dictionary.

    Raises:
        ManifestError: If the file is missing, malformed, or invalid.

    Example:
        >>> manifest = load_manifest(Path("data/survey-manifest.json"))
        >>> manifest["review_points"][0]["id"]
        'G1'
    """
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ManifestError(f"Survey manifest not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ManifestError(f"Survey manifest is invalid JSON: {path}") from error

    errors = validate_manifest(manifest)
    if errors:
        raise ManifestError("; ".join(errors))
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return structural validation errors for a survey review manifest.

    Args:
        manifest: Candidate manifest dictionary.

    Returns:
        A list of human-readable validation errors. An empty list means valid.

    Example:
        >>> validate_manifest({})
        ['manifest must contain source metadata', 'manifest must contain review_points']
    """
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]

    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append("manifest must contain source metadata")
    else:
        for key in ("repository", "branch", "commit", "version"):
            if not isinstance(source.get(key), str) or not source[key]:
                errors.append(f"source metadata must contain {key}")

    judgment_options = manifest.get("judgment_options")
    if tuple(judgment_options or ()) != JUDGMENT_OPTIONS:
        errors.append("manifest must define the three tester judgment options")

    review_points = manifest.get("review_points")
    if not isinstance(review_points, list):
        errors.append("manifest must contain review_points")
        return errors

    actual_ids = [point.get("id") for point in review_points if isinstance(point, dict)]
    if actual_ids != list(EXPECTED_REVIEW_POINT_IDS):
        errors.append(
            "review point order must be " + ", ".join(EXPECTED_REVIEW_POINT_IDS)
        )
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("review point IDs must be unique")

    for point in review_points:
        if not isinstance(point, dict):
            errors.append("each review point must be an object")
            continue
        point_id = point.get("id", "<missing>")
        for key in ("section", "type", "title", "prompt", "source_anchor"):
            if not isinstance(point.get(key), str) or not point[key].strip():
                errors.append(f"{point_id} must contain non-empty {key}")
        if not isinstance(point.get("options"), list):
            errors.append(f"{point_id} options must be a list")
        if point_id == "G2":
            parts = point.get("parts")
            part_ids = [
                part.get("id") for part in parts or [] if isinstance(part, dict)
            ]
            if part_ids != ["G2-use", "G2-governance"]:
                errors.append("G2 must contain use and governance parts")
            if len(parts or []) != 2:
                errors.append("G2 must contain exactly two parts")

    return errors
