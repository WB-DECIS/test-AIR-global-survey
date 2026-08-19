"""Tests for locked, lossless JSONL submission persistence."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.storage import DuplicateSubmissionError, StorageError, SubmissionStore


def _record(submission_id: str) -> dict[str, object]:
    """Build a storage fixture containing escaped user text."""
    return {
        "submission_id": submission_id,
        "tester_email": "gcarletto@worldbank.org",
        "comment": 'Use a clearer label: "formal".\nSecond line.',
    }


def test_append_writes_one_parseable_utf8_json_line(tmp_path: Path) -> None:
    """A valid record is lossless and occupies exactly one JSONL line."""
    path = tmp_path / "responses.jsonl"
    store = SubmissionStore(path)

    store.append(_record("one"))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == _record("one")


def test_duplicate_submission_id_is_rejected(tmp_path: Path) -> None:
    """Retrying the same submission cannot create a second record."""
    store = SubmissionStore(tmp_path / "responses.jsonl")
    store.append(_record("one"))

    with pytest.raises(DuplicateSubmissionError):
        store.append(_record("one"))


def test_missing_response_directory_fails_loudly(tmp_path: Path) -> None:
    """Storage must not silently fall back when its configured directory is absent."""
    store = SubmissionStore(tmp_path / "missing" / "responses.jsonl")

    with pytest.raises(StorageError, match="response directory"):
        store.append(_record("one"))


def test_concurrent_appends_do_not_interleave(tmp_path: Path) -> None:
    """POSIX locking keeps concurrent completed submissions parseable."""
    path = tmp_path / "responses.jsonl"

    def append_one(index: int) -> None:
        SubmissionStore(path).append(_record(f"submission-{index}"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(append_one, range(8)))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8
    assert {json.loads(line)["submission_id"] for line in lines} == {
        f"submission-{index}" for index in range(8)
    }
