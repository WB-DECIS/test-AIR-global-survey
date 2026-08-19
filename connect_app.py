"""Posit Connect entry point for the Git-backed FastAPI application.

Created: 2026-08-19
"""

import os
import secrets
from pathlib import Path

CONTENT_ROOT = Path(__file__).resolve().parent

# Connect does not allow this publisher account to edit runtime variables.
# Keep these defaults scoped to the Connect entry point; local startup still
# requires explicit settings through app.main.
os.environ.setdefault("APP_SESSION_SECRET", secrets.token_urlsafe(48))
os.environ.setdefault(
	"RESPONSE_PATH", str(CONTENT_ROOT / "data/responses/submissions.jsonl")
)
os.environ.setdefault(
	"SURVEY_MANIFEST_PATH", str(CONTENT_ROOT / "data/survey-manifest.json")
)
os.environ.setdefault(
	"ALLOWED_TESTERS_PATH", str(CONTENT_ROOT / "config/allowed-testers.json")
)

from app.main import create_app  # noqa: E402

app = create_app()
