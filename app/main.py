"""FastAPI application for the global survey question-testing pilot."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.access import load_allowed_testers, normalize_email
from app.config import Settings, get_settings
from app.domain.manifest import load_manifest
from app.domain.validation import PayloadValidationError, validate_submission
from app.schemas import AccessRequest, SubmissionPayload
from app.storage import DuplicateSubmissionError, StorageError, SubmissionStore

SESSION_EMAIL_KEY = "tester_email"
SESSION_STARTED_KEY = "session_started_at"
WEB_DIR = Path(__file__).resolve().parent / "web"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def _require_tester(request: Request) -> str:
    """Return the normalized session tester or raise an access error."""
    tester_email = request.session.get(SESSION_EMAIL_KEY)
    if not isinstance(tester_email, str) or not tester_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Approved tester access is required.",
        )
    return tester_email


def _build_submission_record(
    tester_email: str,
    payload: SubmissionPayload,
    manifest: dict[str, Any],
    session_started_at: str | None,
) -> dict[str, Any]:
    """Add server-controlled identity, time, and source metadata to a payload."""
    return {
        "submission_id": str(payload.submission_id),
        "tester_email": tester_email,
        "submitted_at": _utc_now().isoformat(),
        "session_started_at": session_started_at
        or (
            payload.session_started_at.isoformat()
            if payload.session_started_at is not None
            else None
        ),
        "source": manifest["source"],
        "review_points": [
            {
                "id": review_point.id,
                "section": review_point.section,
                "type": review_point.type,
                "judgment": review_point.judgment,
                "comment": review_point.comment,
            }
            for review_point in payload.review_points
        ],
        "general_feedback": payload.general_feedback.model_dump(),
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured FastAPI application instance.

    Args:
        settings: Optional explicit settings, primarily for isolated tests.

    Returns:
        Configured FastAPI application.

    Raises:
        pydantic.ValidationError: If environment-backed settings are incomplete.
        ValueError: If the local manifest or allowlist is invalid.

    Example:
        >>> application = create_app(
        ...     Settings(
        ...         app_session_secret="test",
        ...         response_path=Path("responses.jsonl"),
        ...     )
        ... )
    """
    resolved_settings = settings or get_settings()
    manifest = load_manifest(resolved_settings.survey_manifest_path)
    testers = load_allowed_testers(resolved_settings.allowed_testers_path)
    store = SubmissionStore(resolved_settings.response_path)

    application = FastAPI(
        title="Global Survey Question Testing",
        description="Controlled pilot feedback collection for the global survey draft.",
        version="0.1.0",
    )
    application.add_middleware(
        SessionMiddleware,
        secret_key=resolved_settings.app_session_secret,
        https_only=resolved_settings.secure_cookies,
        same_site="lax",
        max_age=60 * 60 * 8,
    )
    application.state.settings = resolved_settings
    application.state.manifest = manifest
    application.state.testers = testers
    application.state.store = store
    application.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Serve the tester application shell."""
        return FileResponse(WEB_DIR / "index.html")

    @application.get("/review", include_in_schema=False)
    def review() -> FileResponse:
        """Serve the tester application at the Connect-compatible route."""
        return FileResponse(WEB_DIR / "index.html")

    @application.get("/health")
    def health() -> dict[str, str]:
        """Return a data-free liveness response."""
        return {"status": "ok"}

    @application.post("/api/access")
    def access(request: Request, access_request: AccessRequest) -> dict[str, Any]:
        """Establish a signed session for one approved email identifier."""
        normalized_email = normalize_email(access_request.email)
        tester = testers.get(normalized_email)
        if tester is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This email is not approved for the pilot.",
            )
        request.session[SESSION_EMAIL_KEY] = normalized_email
        request.session[SESSION_STARTED_KEY] = _utc_now().isoformat()
        return {"tester": tester}

    @application.get("/api/session")
    def session(request: Request) -> dict[str, Any]:
        """Return the current pilot identity without exposing survey data."""
        tester_email = _require_tester(request)
        return {"tester": testers[tester_email]}

    @application.get("/api/manifest")
    def manifest_route(request: Request) -> dict[str, Any]:
        """Return the protected normalized survey review manifest."""
        _require_tester(request)
        return manifest

    @application.post("/api/submissions")
    def submit(request: Request, payload: SubmissionPayload) -> dict[str, str]:
        """Validate and persist one complete tester review."""
        tester_email = _require_tester(request)
        try:
            validate_submission(payload, manifest)
        except PayloadValidationError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(error),
            ) from error

        record = _build_submission_record(
            tester_email=tester_email,
            payload=payload,
            manifest=manifest,
            session_started_at=request.session.get(SESSION_STARTED_KEY),
        )
        try:
            store.append(record)
        except DuplicateSubmissionError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except StorageError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The response could not be saved. Please retry.",
            ) from error
        return {"status": "saved", "submission_id": record["submission_id"]}

    return application


app = create_app()
