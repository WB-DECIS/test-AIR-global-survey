"""Tests for server-side review payload validation."""

from copy import deepcopy
from pathlib import Path

import pytest

from app.domain.manifest import load_manifest
from app.domain.validation import PayloadValidationError, validate_submission
from app.schemas import GeneralFeedback, ReviewFeedback, SubmissionPayload

ROOT = Path(__file__).resolve().parents[1]


def _valid_payload() -> SubmissionPayload:
    """Build a complete valid payload for validation tests."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    return SubmissionPayload(
        submission_id="00000000-0000-4000-8000-000000000001",
        review_points=[
            ReviewFeedback(
                id=point["id"],
                section=point["section"],
                type=point["type"],
                judgment="Good question",
                comment=None,
            )
            for point in manifest["review_points"]
        ],
        general_feedback=GeneralFeedback(),
    )


def test_complete_payload_is_accepted_against_manifest() -> None:
    """Every manifest review point is required exactly once."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")

    assert validate_submission(_valid_payload(), manifest) is True


def test_missing_review_point_is_rejected() -> None:
    """A tester cannot submit while one required judgment is absent."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    payload = _valid_payload()
    payload.review_points = payload.review_points[:-1]

    with pytest.raises(PayloadValidationError, match="missing review points"):
        validate_submission(payload, manifest)


def test_unknown_judgment_is_rejected() -> None:
    """Only the three explicit tester judgments are valid."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    payload = _valid_payload()
    payload.review_points[0] = payload.review_points[0].model_copy(
        update={"judgment": "Maybe"}
    )

    with pytest.raises(PayloadValidationError, match="invalid judgment"):
        validate_submission(payload, manifest)


def test_duplicate_review_point_is_rejected() -> None:
    """Duplicate IDs must not create ambiguous stored feedback."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    payload = _valid_payload()
    duplicate = deepcopy(payload.review_points[0])
    payload.review_points.append(duplicate)

    with pytest.raises(PayloadValidationError, match="duplicate review points"):
        validate_submission(payload, manifest)
