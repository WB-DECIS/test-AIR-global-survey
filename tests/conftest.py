"""Shared test environment setup for isolated application imports."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

os.environ.setdefault("APP_SESSION_SECRET", "test-session-secret")
os.environ.setdefault(
    "RESPONSE_PATH",
    str(Path(tempfile.gettempdir()) / "global-survey-test-responses.jsonl"),
)
os.environ.setdefault("SURVEY_MANIFEST_PATH", str(ROOT / "data/survey-manifest.json"))
os.environ.setdefault("ALLOWED_TESTERS_PATH", str(ROOT / "config/allowed-testers.json"))
