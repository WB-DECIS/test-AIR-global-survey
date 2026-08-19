"""Application settings loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the single-instance pilot application.

    Args:
        app_session_secret: Secret used to sign the pilot session cookie.
        response_path: Absolute or repository-relative JSONL response path.
        survey_manifest_path: Local normalized survey manifest path.
        allowed_testers_path: Local approved tester configuration path.
        secure_cookies: Whether session cookies require HTTPS.
        max_comment_length: Maximum length for one optional item comment.
        max_general_feedback_length: Maximum length for one final feedback field.

    Example:
        >>> Settings(app_session_secret="test", response_path=Path("responses.jsonl"))
    """

    app_session_secret: str = Field(min_length=1)
    response_path: Path
    survey_manifest_path: Path = Path("data/survey-manifest.json")
    allowed_testers_path: Path = Path("config/allowed-testers.json")
    secure_cookies: bool = False
    max_comment_length: int = Field(default=2000, ge=1, le=10000)
    max_general_feedback_length: int = Field(default=3000, ge=1, le=10000)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Load required application settings from the environment.

    Returns:
        Validated runtime settings.

    Raises:
        pydantic.ValidationError: If required settings are missing or invalid.

    Example:
        >>> settings = get_settings()
        >>> settings.response_path
    """
    return Settings()
