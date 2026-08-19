"""Import and verify the pinned upstream global survey artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY = "https://github.com/zander-prinsloo/AI-Readiness-of-NSOs"
DEFAULT_REF = "research/global-nso-ai-readiness-survey"
DEFAULT_COMMIT = "fa031bae8ac7f85a88bc989846944b6363cf03e3"
DEFAULT_SOURCE_PATHS = {
    "global-survey/instrument/global-nso-ai-readiness-survey-draft.md": (
        "data/source/global-nso-ai-readiness-survey-draft.md"
    ),
    "global-survey/instrument/response-codes.json": "data/source/response-codes.json",
}


class SourceImportError(RuntimeError):
    """Raised when a pinned survey source cannot be verified or imported."""


def load_source_metadata(metadata_path: Path) -> dict[str, Any]:
    """Load source provenance metadata from JSON.

    Args:
        metadata_path: Path to the checked-in provenance metadata.

    Returns:
        Parsed source metadata.

    Raises:
        SourceImportError: If the file is missing or malformed.

    Example:
        >>> load_source_metadata(Path("data/source/source-metadata.json"))["version"]
        '0.1.0-draft'
    """
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SourceImportError(
            f"Source metadata not found: {metadata_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise SourceImportError(
            f"Source metadata is invalid JSON: {metadata_path}"
        ) from error


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    Raises:
        SourceImportError: If the file does not exist.

    Example:
        >>> len(sha256_file(Path("data/source/response-codes.json")))
        64
    """
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source_file:
            for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError as error:
        raise SourceImportError(f"Pinned source file not found: {path}") from error
    return digest.hexdigest()


def verify_source_files(repository_root: Path, metadata: dict[str, Any]) -> bool:
    """Verify every checked-in source file against its recorded hash.

    Args:
        repository_root: Root directory containing the local source paths.
        metadata: Provenance metadata with a ``files`` mapping.

    Returns:
        ``True`` when every recorded file matches.

    Raises:
        SourceImportError: If metadata is incomplete or any hash mismatches.

    Example:
        >>> verify_source_files(Path('.'), metadata)
        True
    """
    files = metadata.get("files")
    if not isinstance(files, dict) or not files:
        raise SourceImportError("Source metadata must contain a non-empty files map")

    for remote_path, file_metadata in files.items():
        if not isinstance(file_metadata, dict):
            raise SourceImportError(f"Invalid metadata for source file: {remote_path}")
        local_path_value = file_metadata.get("local_path")
        expected_hash = file_metadata.get("sha256")
        if not isinstance(local_path_value, str) or not isinstance(expected_hash, str):
            raise SourceImportError(
                f"Incomplete metadata for source file: {remote_path}"
            )
        actual_hash = sha256_file(repository_root / local_path_value)
        if actual_hash != expected_hash:
            raise SourceImportError(
                f"Source hash mismatch for {remote_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
    return True


def _raw_url(repository: str, commit: str, source_path: str) -> str:
    """Build the raw GitHub URL for a pinned source path."""
    repository_path = repository.rstrip("/").removeprefix("https://github.com/")
    return f"https://raw.githubusercontent.com/{repository_path}/{commit}/{source_path}"


def _fetch_source(url: str) -> bytes:
    """Fetch one public source artifact without following redirects."""
    try:
        import httpx
    except ImportError as error:
        raise SourceImportError(
            "httpx is required to import source artifacts; install requirements.txt"
        ) from error

    try:
        with httpx.Client(follow_redirects=False, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise SourceImportError(f"Unable to fetch pinned source: {url}") from error
    return response.content


def import_source_artifacts(
    repository: str = DEFAULT_REPOSITORY,
    ref: str = DEFAULT_REF,
    commit: str = DEFAULT_COMMIT,
    source_paths: dict[str, str] | None = None,
    repository_root: Path = Path("."),
    metadata_path: Path = Path("data/source/source-metadata.json"),
    retrieved_at: str | None = None,
    allow_update: bool = False,
) -> dict[str, Any]:
    """Fetch, pin, and record the exact upstream survey artifacts.

    Args:
        repository: Public source repository URL.
        ref: Human-readable source branch or ref recorded for provenance.
        commit: Immutable source commit to fetch.
        source_paths: Mapping from remote paths to repository-relative paths.
        repository_root: Destination repository root.
        metadata_path: Repository-relative provenance metadata path.
        retrieved_at: ISO date to record; defaults to the current UTC date.
        allow_update: Permit replacing an existing source vintage explicitly.

    Returns:
        The newly written provenance metadata.

    Raises:
        SourceImportError: If fetching, validation, or safe vintage replacement fails.

    Example:
        >>> metadata = import_source_artifacts(retrieved_at="2026-08-19")
        >>> metadata["commit"]
        'fa031bae8ac7f85a88bc989846944b6363cf03e3'
    """
    selected_paths = source_paths or DEFAULT_SOURCE_PATHS
    if not selected_paths:
        raise SourceImportError("At least one source path is required")

    downloaded: dict[str, bytes] = {}
    for remote_path in selected_paths:
        downloaded[remote_path] = _fetch_source(
            _raw_url(repository, commit, remote_path)
        )

    retrieved_date = retrieved_at or date.today().isoformat()
    metadata: dict[str, Any] = {
        "created": datetime.now(UTC).date().isoformat(),
        "repository": repository,
        "branch": ref,
        "commit": commit,
        "version": "unknown",
        "retrieved_at": retrieved_date,
        "files": {},
    }

    for remote_path, local_path_value in selected_paths.items():
        content = downloaded[remote_path]
        local_path = repository_root / local_path_value
        local_path.parent.mkdir(parents=True, exist_ok=True)
        metadata["files"][remote_path] = {
            "local_path": local_path_value,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    draft_path = next(
        (
            repository_root / item["local_path"]
            for remote_path, item in metadata["files"].items()
            if remote_path.endswith("global-nso-ai-readiness-survey-draft.md")
        ),
        None,
    )
    if draft_path is not None:
        frontmatter = (
            downloaded[
                next(
                    remote_path
                    for remote_path in selected_paths
                    if remote_path.endswith("global-nso-ai-readiness-survey-draft.md")
                )
            ]
            .decode("utf-8")
            .split("---", 2)[1]
        )
        for line in frontmatter.splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip() == "version":
                metadata["version"] = value.strip().strip('"')
                break

    metadata_file = repository_root / metadata_path
    if metadata_file.exists() and not allow_update:
        existing = load_source_metadata(metadata_file)
        if (
            existing.get("commit") != commit
            or existing.get("files") != metadata["files"]
        ):
            raise SourceImportError(
                "Pinned source vintage differs from existing metadata; "
                "rerun with --allow-update to change the vintage"
            )

    for remote_path, local_path_value in selected_paths.items():
        (repository_root / local_path_value).write_bytes(downloaded[remote_path])
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the source importer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--commit", default=DEFAULT_COMMIT)
    parser.add_argument("--retrieved-at", default=None)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=Path("data/source/source-metadata.json"),
    )
    parser.add_argument("--allow-update", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the source importer and return a process exit code."""
    args = _parse_args()
    import_source_artifacts(
        repository=args.repository,
        ref=args.ref,
        commit=args.commit,
        repository_root=args.repository_root,
        metadata_path=args.metadata_path,
        retrieved_at=args.retrieved_at,
        allow_update=args.allow_update,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
