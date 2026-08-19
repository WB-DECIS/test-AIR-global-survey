"""Pydantic schemas crossing the HTTP and persistence boundaries."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Judgment = Literal["Good question", "Bad question", "Needs refinement"]
ReviewPointType = Literal["question", "instruction"]


class AccessRequest(BaseModel):
    """Request body for the low-friction pilot access gate."""

    email: str = Field(min_length=3, max_length=320)


class ReviewFeedback(BaseModel):
    """One required tester judgment and optional comment."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=64)
    section: str = Field(min_length=1, max_length=100)
    type: ReviewPointType
    judgment: Judgment
    comment: str | None = Field(default=None, max_length=2000)


class GeneralFeedback(BaseModel):
    """Optional final prompts from the cognitive-testing workflow."""

    model_config = ConfigDict(extra="forbid")

    missing_questions: str | None = Field(default=None, max_length=3000)
    survey_length: str | None = Field(default=None, max_length=3000)
    difficult_items: str | None = Field(default=None, max_length=3000)
    duplicative_items: str | None = Field(default=None, max_length=3000)
    translation_terms: str | None = Field(default=None, max_length=3000)
    product_selection: str | None = Field(default=None, max_length=3000)
    overall_burden: str | None = Field(default=None, max_length=3000)
    other_comments: str | None = Field(default=None, max_length=3000)


class SubmissionPayload(BaseModel):
    """Complete client submission before server provenance is added."""

    model_config = ConfigDict(extra="forbid")

    submission_id: UUID
    session_started_at: datetime | None = None
    review_points: list[ReviewFeedback] = Field(min_length=1)
    general_feedback: GeneralFeedback = Field(default_factory=GeneralFeedback)
