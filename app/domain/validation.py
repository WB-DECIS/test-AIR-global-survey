"""Server-side validation derived from the pinned survey manifest."""

from __future__ import annotations

from typing import Any

from app.domain.manifest import JUDGMENT_OPTIONS
from app.schemas import SubmissionPayload


class PayloadValidationError(ValueError):
    """Raised when submitted review feedback does not match the manifest."""


def validate_submission(payload: SubmissionPayload, manifest: dict[str, Any]) -> bool:
    """Validate review IDs, order, metadata, and tester judgments.

    Args:
        payload: Parsed client submission.
        manifest: Validated local survey manifest.

    Returns:
        ``True`` when the complete payload is acceptable.

    Raises:
        PayloadValidationError: If a required review point is missing, duplicated,
            unknown, out of order, or inconsistent with the manifest.

    Example:
        >>> validate_submission(payload, manifest)
        True
    """
    expected_points = manifest["review_points"]
    expected_ids = [point["id"] for point in expected_points]
    actual_ids = [point.id for point in payload.review_points]
    duplicates = sorted(
        {point_id for point_id in actual_ids if actual_ids.count(point_id) > 1}
    )
    if duplicates:
        raise PayloadValidationError(
            "duplicate review points: " + ", ".join(duplicates)
        )

    missing = [point_id for point_id in expected_ids if point_id not in actual_ids]
    if missing:
        raise PayloadValidationError("missing review points: " + ", ".join(missing))

    unknown = [point_id for point_id in actual_ids if point_id not in expected_ids]
    if unknown:
        raise PayloadValidationError("unknown review points: " + ", ".join(unknown))

    if actual_ids != expected_ids:
        raise PayloadValidationError("review points must follow manifest order")

    expected_by_id = {point["id"]: point for point in expected_points}
    for review_point in payload.review_points:
        expected = expected_by_id[review_point.id]
        if review_point.section != expected["section"]:
            raise PayloadValidationError(
                f"section mismatch for review point {review_point.id}"
            )
        if review_point.type != expected["type"]:
            raise PayloadValidationError(
                f"type mismatch for review point {review_point.id}"
            )
        if review_point.judgment not in JUDGMENT_OPTIONS:
            raise PayloadValidationError(
                f"invalid judgment for review point {review_point.id}"
            )
        if review_point.comment is not None and not isinstance(
            review_point.comment, str
        ):
            raise PayloadValidationError(
                f"comment must be text for review point {review_point.id}"
            )
    return True
