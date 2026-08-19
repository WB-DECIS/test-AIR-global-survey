"""Tests for protected FastAPI routes and access flow."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


def _client(tmp_path: Path) -> TestClient:
    """Build an isolated API client for one test."""
    settings = Settings(
        app_session_secret="test-session-secret",
        response_path=tmp_path / "responses.jsonl",
        survey_manifest_path=ROOT / "data/survey-manifest.json",
        allowed_testers_path=ROOT / "config/allowed-testers.json",
        secure_cookies=False,
    )
    return TestClient(create_app(settings))


def test_health_endpoint_is_public_and_does_not_expose_data(tmp_path: Path) -> None:
    """Health checks should reveal only service liveness."""
    response = _client(tmp_path).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_review_route_serves_the_tester_application(tmp_path: Path) -> None:
    """The Connect-compatible review path serves the HTML application shell."""
    response = _client(tmp_path).get("/review")

    assert response.status_code == 200
    assert "Global survey review" in response.text


def test_manifest_requires_an_approved_session(tmp_path: Path) -> None:
    """Survey content must not be available before allowlist entry."""
    response = _client(tmp_path).get("/api/manifest")

    assert response.status_code == 401


def test_approved_email_receives_access_and_manifest(tmp_path: Path) -> None:
    """An approved identifier should receive a session and the local manifest."""
    client = _client(tmp_path)

    access_response = client.post(
        "/api/access", json={"email": " GCARLETTO@WORLDBANK.ORG "}
    )
    manifest_response = client.get("/api/manifest")

    assert access_response.status_code == 200
    assert access_response.json()["tester"]["email"] == "gcarletto@worldbank.org"
    assert manifest_response.status_code == 200
    assert len(manifest_response.json()["review_points"]) == 16


def test_unapproved_email_is_rejected(tmp_path: Path) -> None:
    """An unapproved identifier cannot establish a pilot session."""
    response = _client(tmp_path).post(
        "/api/access", json={"email": "other@example.org"}
    )

    assert response.status_code == 403


def test_complete_review_submission_is_stored_with_server_provenance(
    tmp_path: Path,
) -> None:
    """The API stores the review judgments, comments, and source metadata."""
    client = _client(tmp_path)
    client.post("/api/access", json={"email": "gcarletto@worldbank.org"})
    manifest = client.get("/api/manifest").json()
    payload = {
        "submission_id": "00000000-0000-4000-8000-000000000002",
        "review_points": [
            {
                "id": point["id"],
                "section": point["section"],
                "type": point["type"],
                "judgment": "Needs refinement"
                if point["id"] == "G1"
                else "Good question",
                "comment": "Clarify this wording." if point["id"] == "G1" else None,
            }
            for point in manifest["review_points"]
        ],
        "general_feedback": {
            "survey_length": "About right",
            "other_comments": "Please keep the review flow quick.",
        },
    }

    response = client.post("/api/submissions", json=payload)

    assert response.status_code == 200
    stored_line = (
        (tmp_path / "responses.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    stored = json.loads(stored_line)
    assert stored["tester_email"] == "gcarletto@worldbank.org"
    assert stored["source"]["commit"] == "fa031bae8ac7f85a88bc989846944b6363cf03e3"
    assert stored["review_points"][0]["comment"] == "Clarify this wording."


def test_invalid_feedback_judgment_is_rejected_by_http_schema(tmp_path: Path) -> None:
    """The HTTP boundary rejects labels outside the three feedback choices."""
    client = _client(tmp_path)
    client.post("/api/access", json={"email": "gcarletto@worldbank.org"})
    manifest = client.get("/api/manifest").json()
    payload = {
        "submission_id": "00000000-0000-4000-8000-000000000003",
        "review_points": [
            {
                "id": point["id"],
                "section": point["section"],
                "type": point["type"],
                "judgment": "Maybe",
            }
            for point in manifest["review_points"]
        ],
        "general_feedback": {},
    }

    response = client.post("/api/submissions", json=payload)

    assert response.status_code == 422
