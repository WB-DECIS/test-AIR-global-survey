# Global Survey Question-Testing Application

<!-- Created: 2026-08-19 -->

This repository contains a small controlled pilot application for reviewing the
draft Global NSO AI-Readiness Survey. It collects design feedback about the
question wording, response options, and instructions. It does **not** collect
answers to the underlying NSO survey and it does not calculate scores.

## Pilot Access

The entry gate accepts only these six approved email identifiers:

- `gcarletto@worldbank.org`
- `asolatorio@worldbank.org`
- `zprinsloo@worldbank.org`
- `userajuddin@worldbank.org`
- `dmahler@worldbank.org`
- `hdang@worldbank.org`

The gate is case-insensitive and trims surrounding whitespace. It is an
allowlist identifier check, not authentication. Anyone who knows an approved
email could enter, so use the application only in the controlled pilot context.
The application does not include World Bank SSO, passwords, or magic links.

## Survey Vintage

The exact tested source is pinned locally:

- Repository: `https://github.com/zander-prinsloo/AI-Readiness-of-NSOs`
- Branch: `research/global-nso-ai-readiness-survey`
- Commit: `fa031bae8ac7f85a88bc989846944b6363cf03e3`
- Draft version: `0.1.0-draft`
- Source files: `data/source/global-nso-ai-readiness-survey-draft.md` and
	`data/source/response-codes.json`

`data/source/source-metadata.json` records the retrieval date and SHA-256
hashes. The normalized runtime manifest is `data/survey-manifest.json`. It
contains 16 ordered review points: G1, G2, Q1-Q7, the Q8-Q11 product-reference
instruction, Q8-Q11, Q12, and optional evidence guidance. The app reads these
checked-in files and never fetches survey content at runtime.

## Local Setup

This project uses Python and `uv`.

```text
uv sync --dev
cp .env.example .env
```

Set `APP_SESSION_SECRET` in `.env` to a long random value generated outside the
repository. The remaining example values work for a checkout from the project
root:

```text
RESPONSE_PATH=data/responses/submissions.jsonl
SURVEY_MANIFEST_PATH=data/survey-manifest.json
ALLOWED_TESTERS_PATH=config/allowed-testers.json
SECURE_COOKIES=false
```

Run the server:

```text
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` in a browser.

For hosted HTTPS deployment, set `SECURE_COOKIES=true` and provide a response
path on persistent POSIX storage. The pilot storage model assumes one app
instance; multi-instance deployment requires an explicitly approved storage
change.

## Source Import

To verify the current pinned source or import a new explicitly approved vintage:

```text
uv run python -m scripts.import_survey \
	--commit fa031bae8ac7f85a88bc989846944b6363cf03e3
```

The importer fails if the existing vintage differs. Changing the source requires
`--allow-update`, a manifest update, and a new review of the resulting wording.

## Testing

Install the browser runtime once:

```text
uv run playwright install chromium
```

Run the complete test suite:

```text
uv run pytest -q
uv run ruff check app scripts tests
uv run python -m compileall app scripts
```

The tests cover source hashes and text fidelity, allowlist behavior, protected
routes, payload validation, JSONL locking and escaping, duplicate submissions,
keyboard-friendly navigation, optional comments, final feedback, and desktop
and mobile browser completion. Browser tests use temporary response paths and
do not write pilot data.

## Stored Feedback

Completed submissions are written to
`data/responses/submissions.jsonl`, one parseable JSON object per line. The file
contains the tester email, server timestamps, source provenance, every ordered
judgment, optional item comments, and optional general feedback. The writer
uses an exclusive POSIX lock, flush, and `fsync`; it fails loudly when the
configured response directory is unavailable. Response files and `.env` are
ignored by Git.

## Out Of Scope

- Underlying NSO survey answers, scoring, analytics, rankings, or maturity levels.
- An admin dashboard, response browser, export UI, or survey editor.
- Resume-later/server-side drafts or multi-instance storage.
- Strong authentication such as SSO, passwords, or email magic links.
- Runtime fetching, editing, paraphrasing, or translation of the source survey.
