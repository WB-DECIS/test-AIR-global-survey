"""Tests for the normalized survey review manifest."""

import re
from pathlib import Path

from app.domain.manifest import (
    EXPECTED_REVIEW_POINT_IDS,
    load_manifest,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_preserves_full_review_order_and_source_contract() -> None:
    """Every survey item and review instruction appears once in source order."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")

    assert [point["id"] for point in manifest["review_points"]] == list(
        EXPECTED_REVIEW_POINT_IDS
    )
    assert len(manifest["review_points"]) == 16
    assert manifest["source"]["version"] == "0.1.0-draft"
    assert manifest["review_points"][0]["id"] == "G1"
    assert manifest["review_points"][1]["id"] == "G2"
    assert manifest["review_points"][1]["parts"][0]["id"] == "G2-use"
    assert manifest["review_points"][1]["parts"][1]["id"] == "G2-governance"
    assert manifest["review_points"][9]["id"] == "product-reference"
    assert manifest["review_points"][-1]["id"] == "optional-evidence"


def test_manifest_validation_rejects_duplicate_or_missing_review_points() -> None:
    """Manifest validation must reject structural drift before runtime use."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    manifest["review_points"] = manifest["review_points"][:-1]

    errors = validate_manifest(manifest)

    assert any("review point order" in error for error in errors)


def test_manifest_text_and_options_are_present_in_pinned_draft() -> None:
    """Manifest content must be drawn from the exact checked-in draft text."""
    manifest = load_manifest(ROOT / "data/survey-manifest.json")
    draft_text = (
        ROOT / "data/source/global-nso-ai-readiness-survey-draft.md"
    ).read_text(encoding="utf-8")
    normalized_draft = re.sub(r"\s+", " ", draft_text).strip()

    for point in manifest["review_points"]:
        assert point["source_anchor"] in draft_text
        assert re.sub(r"\s+", " ", point["prompt"]).strip() in normalized_draft
        for option in point["options"]:
            assert re.sub(r"\s+", " ", option).strip() in normalized_draft
        for part in point.get("parts", []):
            assert part["label"] in draft_text
            for option in part["options"]:
                assert re.sub(r"\s+", " ", option).strip() in normalized_draft
