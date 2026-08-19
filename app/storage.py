"""Lossless, locked JSON Lines persistence for completed pilot submissions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError as error:  # pragma: no cover - the pilot target is POSIX.
    raise RuntimeError("JSONL storage requires a POSIX host with fcntl") from error


class StorageError(RuntimeError):
    """Raised when a submission cannot be safely persisted."""


class DuplicateSubmissionError(StorageError):
    """Raised when a submission ID has already been stored."""


class SubmissionStore:
    """Append validated submission records to one locked JSONL file."""

    def __init__(self, path: Path) -> None:
        """Initialize a store for one configured response file.

        Args:
            path: JSONL response path.

        Example:
            >>> store = SubmissionStore(Path("data/responses/submissions.jsonl"))
        """
        self.path = path

    def append(self, record: dict[str, Any]) -> None:
        """Append one record after checking identity uniqueness.

        Args:
            record: Complete server-side submission record.

        Raises:
            DuplicateSubmissionError: If the submission ID already exists.
            StorageError: If the directory or write operation is unavailable.

        Example:
            >>> store.append({"submission_id": "one"})
        """
        submission_id = record.get("submission_id")
        if not isinstance(submission_id, str) or not submission_id:
            raise StorageError("submission record must contain a submission_id")
        parent = self.path.parent
        if not parent.exists() or not parent.is_dir():
            raise StorageError(f"response directory does not exist: {parent}")

        serialized = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        try:
            with self.path.open("a+", encoding="utf-8") as response_file:
                fcntl.flock(response_file.fileno(), fcntl.LOCK_EX)
                try:
                    response_file.seek(0)
                    for line_number, line in enumerate(response_file, start=1):
                        if not line.strip():
                            continue
                        try:
                            existing = json.loads(line)
                        except json.JSONDecodeError as error:
                            raise StorageError(
                                f"invalid existing JSONL at line {line_number}"
                            ) from error
                        if existing.get("submission_id") == submission_id:
                            raise DuplicateSubmissionError(
                                f"submission already stored: {submission_id}"
                            )
                    response_file.seek(0, os.SEEK_END)
                    response_file.write(serialized + "\n")
                    response_file.flush()
                    os.fsync(response_file.fileno())
                finally:
                    fcntl.flock(response_file.fileno(), fcntl.LOCK_UN)
        except DuplicateSubmissionError:
            raise
        except OSError as error:
            raise StorageError(f"unable to write response file: {self.path}") from error
