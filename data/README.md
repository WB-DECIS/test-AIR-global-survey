# Application Data

<!-- Created: 2026-08-19 -->

## Source

The runtime survey content is checked in under `data/source/` and summarized in
`data/survey-manifest.json`. The pinned source is:

- Repository: `https://github.com/zander-prinsloo/AI-Readiness-of-NSOs`
- Branch: `research/global-nso-ai-readiness-survey`
- Commit: `fa031bae8ac7f85a88bc989846944b6363cf03e3`
- Draft version: `0.1.0-draft`

`data/source/source-metadata.json` records the source paths, retrieval date, and
SHA-256 hashes. Use `python -m scripts.import_survey` to verify or explicitly
update a source vintage. The application never fetches survey content at runtime.

## Responses

Completed pilot submissions are appended to
`data/responses/submissions.jsonl`. Each line is one UTF-8 JSON object containing:

- server-generated submission and timestamp fields;
- the normalized tester email;
- source repository, branch, commit, version, and source hashes;
- the ordered review-point IDs, sections, types, judgments, and optional comments;
- the optional general-feedback prompts.

The response directory is intentionally outside the static web directory. The
pilot expects one POSIX host and uses an exclusive file lock, flush, and `fsync`
for each append. Back up the response file using the team's approved storage
process. Response files are ignored by Git and must never be committed.
