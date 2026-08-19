"""Tests for pinned survey source provenance and integrity."""

from pathlib import Path

import pytest

from scripts.import_survey import (
    DEFAULT_SOURCE_PATHS,
    SourceImportError,
    import_source_artifacts,
    load_source_metadata,
    verify_source_files,
)

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_source_files_match_recorded_hashes() -> None:
    """The checked-in source bytes must match the recorded upstream hashes."""
    metadata = load_source_metadata(ROOT / "data/source/source-metadata.json")

    assert verify_source_files(ROOT, metadata) is True


def test_source_hash_mismatch_fails_loudly(tmp_path: Path) -> None:
    """A changed source file must not pass provenance validation."""
    metadata = load_source_metadata(ROOT / "data/source/source-metadata.json")
    draft_path = tmp_path / "data/source/global-nso-ai-readiness-survey-draft.md"
    draft_path.parent.mkdir(parents=True)
    draft_path.write_bytes(b"changed")
    response_path = tmp_path / "data/source/response-codes.json"
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_bytes((ROOT / "data/source/response-codes.json").read_bytes())

    with pytest.raises(SourceImportError, match="hash mismatch"):
        verify_source_files(tmp_path, metadata)


def test_import_source_artifacts_preserves_bytes_and_records_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The importer must write exact fetched bytes and auditable metadata."""
    source_bytes = {
        remote_path: (ROOT / local_path).read_bytes()
        for remote_path, local_path in DEFAULT_SOURCE_PATHS.items()
    }

    def fake_fetch(url: str) -> bytes:
        return next(
            content
            for remote_path, content in source_bytes.items()
            if url.endswith(remote_path)
        )

    monkeypatch.setattr("scripts.import_survey._fetch_source", fake_fetch)

    metadata = import_source_artifacts(
        repository="https://github.com/example/project",
        ref="test-ref",
        commit="abc123",
        repository_root=tmp_path,
        metadata_path=Path("data/source/source-metadata.json"),
        retrieved_at="2026-08-19",
    )

    assert metadata["version"] == "0.1.0-draft"
    assert metadata["commit"] == "abc123"
    assert (
        tmp_path / "data/source/global-nso-ai-readiness-survey-draft.md"
    ).read_bytes() == source_bytes[
        next(
            remote_path
            for remote_path in DEFAULT_SOURCE_PATHS
            if remote_path.endswith("global-nso-ai-readiness-survey-draft.md")
        )
    ]
    assert verify_source_files(tmp_path, metadata) is True
