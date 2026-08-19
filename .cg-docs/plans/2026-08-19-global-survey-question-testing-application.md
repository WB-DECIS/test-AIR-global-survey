---
date: 2026-08-19
title: "Global survey question-testing application"
status: completed
completed-date: 2026-08-19
completed-phases: [1, 2, 3, 4]
execution-report: ".cg-docs/work-reports/2026-08-19-global-survey-question-testing-application.md"
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-19-global-survey-testing-application.md"
language: "Python"
estimated-effort: "large"
deviation-policy: "ask"
phases: 4
artifact-schema-version: 1
tags: [global-survey, fastapi, feedback-capture, jsonl, usability-testing]
---
<!-- Created: 2026-08-19 -->

# Plan: Global Survey Question-Testing Application

## Objective

Build a runnable, low-friction web application that lets six approved World Bank testers review the complete AI-readiness global survey draft, record one quick design judgment for every review point, optionally add comments, and submit general feedback. Preserve the exact tested survey vintage and store each completed review as one lossless JSON Lines record.

## Context

The repository currently contains project configuration and Compound GPID artifacts but no application source, dependency manifest, survey data, or tests. The implementation will therefore establish the application structure from scratch while keeping the pilot deliberately narrow.

The authoritative source is the `research/global-nso-ai-readiness-survey` branch of `zander-prinsloo/AI-Readiness-of-NSOs`, specifically `global-survey/instrument/global-nso-ai-readiness-survey-draft.md` and its response-code contract. The source branch head observed for this plan is `fa031bae8ac7f85a88bc989846944b6363cf03e3`. The source package identifies version `0.1.0-draft`, targets roughly 10 to 20 minutes for an informed NSO respondent, and describes a screening instrument rather than field-valid readiness results.

The application is a survey-design review tool, not a survey response collector. Testers will see the exact survey questions, instructions, and response options as read-only content and will select `Good question`, `Bad question`, or `Needs refinement` as feedback about each review point.

## Requirements

| ID | Requirement | Source |
|---|---|---|
| R1 | Preserve the exact draft instrument, response options, ordering, source ref, commit, and version in local versioned data. | Charter; brainstorm; source survey package |
| R2 | Cover the full flow from Gateway through scored questions Q1-Q12, including G2's two parts, the Q8-Q11 product-reference instruction, and optional evidence guidance. | User request; draft instrument |
| R3 | Allow entry only for the six approved email identifiers, using case-insensitive normalization. | User request; brainstorm |
| R4 | Explain the purpose of the global survey, that testers are reviewing it, and that their feedback is recorded. | User request |
| R5 | Require exactly one feedback judgment per review point: `Good question`, `Bad question`, or `Needs refinement`. | User request |
| R6 | Keep written comments optional and never block navigation when they are blank. | User clarification |
| R7 | Collect optional final general feedback about missing questions, length, ambiguity, duplication, translation, burden, and other recommendations. | User request; cognitive-testing protocol; respondent feedback template |
| R8 | Optimize for rapid completion with one clear card at a time, visible progress, back/next controls, keyboard-friendly choices, and retained in-session state. | User clarification; brainstorm |
| R9 | Store one precise completed submission with tester email, timestamps, source metadata, review-point IDs, sections, judgments, comments, and final feedback. | Charter; brainstorm |
| R10 | Fail loudly on missing configuration, invalid source data, invalid payloads, and failed response writes; never silently discard feedback. | Charter; goal-execution contract |
| R11 | Keep the pilot single-pass and single-instance; do not add scoring, analytics, an admin dashboard, an editor, resume-later support, or strong authentication. | Brainstorm decision |
| R12 | Document setup, source provenance, response-file handling, allowlist limitations, deployment assumptions, and verification commands. | Brainstorm; project reproducibility preference |

## Implementation Steps

## Phase 1: Pinned survey data and review contract

### 1. Pin and import the draft instrument

- **Requirements**: R1, R2, R10, R12
- **Files**: `data/source/global-nso-ai-readiness-survey-draft.md`, `data/source/response-codes.json`, `data/source/source-metadata.json`, `scripts/import_survey.py`, `tests/test_source_import.py`
- **Details**: Add a reproducible import script that accepts the repository, branch, commit, and source paths explicitly. Copy the draft Markdown and response-code JSON into a local source directory and write provenance containing the repository URL, branch, commit SHA, source paths, source version, retrieval date, and SHA-256 hashes. Runtime application code must read the checked-in local copy and must not fetch GitHub. The importer must fail when a requested source cannot be retrieved or when an existing pinned hash changes without an explicit source-vintage update.
- **Test Scenarios**: successful import at the recorded commit; missing source; hash mismatch; malformed response contract; source version mismatch.
- **Tests**: `pytest -q tests/test_source_import.py`
- **Acceptance criteria**: The repository contains the exact source artifacts and machine-readable provenance; a fresh import either reproduces the recorded hashes or exits nonzero with an actionable error.

### 2. Build and validate the review-point manifest

- **Requirements**: R1, R2, R5, R8, R9
- **Files**: `data/survey-manifest.json`, `app/domain/__init__.py`, `app/domain/manifest.py`, `tests/test_survey_manifest.py`
- **Details**: Create a normalized manifest used by both the API and UI. Preserve exact display text and read-only survey response options while adding stable review metadata. Use this ordered review-point sequence: `G1`, `G2`, `Q1` through `Q7`, `product-reference`, `Q8` through `Q11`, `Q12`, and `optional-evidence`. Render G2 as one low-friction review card containing its distinct use-pattern and governance subparts, while retaining both subparts in the manifest. Treat the product-reference and optional-evidence instructions as review points so testers can flag unclear instructions as well as question wording. Record each point's source anchor, section, type, display text, options, and any child parts. Keep the app introduction separate from the source survey content.
- **Test Scenarios**: all expected review IDs exist once and in order; every source question has text and options; G2 has both parts; product-reference appears before Q8; optional-evidence appears after Q12; no unapproved survey-answer fields are introduced.
- **Tests**: `pytest -q tests/test_survey_manifest.py`
- **Acceptance criteria**: The manifest validator fails on missing, duplicate, reordered, paraphrased, or structurally incomplete source content and passes for the pinned draft.

## Phase 2: Application core and access boundary

### 3. Establish application configuration, allowlist, and pilot session

- **Requirements**: R3, R10, R11, R12
- **Files**: `app/__init__.py`, `app/config.py`, `app/access.py`, `app/schemas.py`, `app/main.py`, `config/allowed-testers.json`, `requirements.txt`, `requirements-dev.txt`, `.env.example`
- **Details**: Add FastAPI and Uvicorn dependencies, Pydantic settings, and a small configuration layer. Store the six approved email addresses and the provided display name for Gero Carletto in an auditable JSON configuration file; normalize input with trimming and case folding before membership checks. Require an application session secret and response path at startup, with no silent defaults for production-sensitive settings. Use a signed, HTTP-only session cookie only to carry the approved tester identifier after the allowlist check. Mark the email gate clearly as pilot access control rather than authentication; support secure-cookie configuration for hosted deployment.
- **Test Scenarios**: each approved email in mixed case; surrounding whitespace; unapproved address; malformed email; missing session secret; missing response path; cookie/session expiry or invalid signature.
- **Tests**: `pytest -q tests/test_access.py`
- **Acceptance criteria**: Approved identifiers receive a session and all other identifiers receive a clear rejection without access to survey content; missing required configuration prevents startup with an explicit error.

### 4. Define protected API routes and server-side payload validation

- **Requirements**: R3, R5, R6, R7, R9, R10, R11
- **Files**: `app/main.py`, `app/schemas.py`, `app/domain/validation.py`, `tests/test_api.py`, `tests/test_workflow.py`
- **Details**: Implement the access endpoint, protected manifest endpoint, and final submission endpoint. The server must derive the expected review-point IDs and source metadata from its local manifest rather than trusting client-supplied content. Accept only the three judgment labels, require one judgment for every expected review point, reject duplicates, unknown IDs, missing IDs, malformed comments, and invalid general-feedback shapes, and preserve blank optional fields as explicit empty values or nulls according to one documented schema. Add a safe health endpoint that does not expose tester or response data.
- **Test Scenarios**: valid complete payload; missing judgment; duplicate review ID; unknown ID; invalid judgment; oversized text; malformed JSON; submission without an approved session; invalid source-vintage claim; failed storage call with no partial success response.
- **Tests**: `pytest -q tests/test_api.py tests/test_workflow.py`
- **Acceptance criteria**: The API accepts only a complete valid review payload and returns explicit, actionable errors for every invalid case without writing invalid data.

## Phase 3: Tester workflow and response persistence

### 5. Build the access, introduction, and application shell

- **Requirements**: R3, R4, R8, R11
- **Files**: `app/web/index.html`, `app/web/app.js`, `app/web/styles.css`, `app/main.py`
- **Details**: Serve a responsive, accessible vanilla HTML/CSS/JavaScript interface from FastAPI. Start with a compact email entry gate, then show an introduction that states the tester is reviewing the global survey, explains that it is a short screening tool for national statistical offices' AI readiness, and states that feedback is recorded for survey improvement. Include a clear start action and no unnecessary registration, profile, or account setup. Use semantic headings, visible focus states, large labeled controls, a restrained but distinctive visual system, and responsive layout constraints for narrow screens.
- **Test Scenarios**: gate rejection and retry; successful gate; keyboard-only access; narrow viewport; missing API response; refresh before starting.
- **Tests**: API shell tests in `tests/test_workflow.py` plus the browser flow in `tests/e2e/test_review_flow.py`.
- **Acceptance criteria**: An approved tester reaches the introduction in one short interaction, understands the feedback purpose, and can start the review without encountering a dead end or layout overflow.

### 6. Implement sequential review cards and progress state

- **Requirements**: R2, R5, R6, R8, R9, R11
- **Files**: `app/web/app.js`, `app/web/styles.css`, `app/domain/manifest.py`, `tests/e2e/test_review_flow.py`
- **Details**: Render exactly one review card at a time in manifest order. Show the survey section, item ID, exact question or instruction text, and exact read-only response options; visually distinguish the tester feedback controls from the survey's own options. Provide three large radio-card choices labeled `Good question`, `Bad question`, and `Needs refinement`, an optional comment field, a visible `X of Y` progress indicator, and explicit Back and Next controls. Disable Next until the current judgment is selected. Preserve selections and comments in browser session storage for accidental refreshes during the one-pass session, but do not present this as resume-later support. Keep focus on the selected/next control after navigation and retain G2's two displayed parts on one card.
- **Test Scenarios**: full ordered progression; back navigation retains state; blank comment proceeds; Next blocked without judgment; keyboard radio selection; product-reference and optional-evidence cards display in the correct positions; browser refresh restores the current in-session state; malformed manifest fails visibly.
- **Tests**: `pytest -q tests/e2e/test_review_flow.py`
- **Acceptance criteria**: A tester can review every point with one obvious required action per card, never has to answer the underlying survey, and can move backward without losing entered feedback.

### 7. Add general feedback, submission, and completion states

- **Requirements**: R7, R8, R9, R10, R11
- **Files**: `app/web/app.js`, `app/web/styles.css`, `app/web/index.html`, `tests/e2e/test_review_flow.py`, `tests/test_api.py`
- **Details**: Add a final optional feedback page with prompts for missing questions, survey length, difficult or ambiguous items, duplicative items, terms needing translation or explanation, product-selection difficulty, overall burden, and other comments. Show a concise review summary before submission, disable the submit control while the request is in flight, and prevent accidental duplicate submissions after success. On a failed write, preserve the in-browser payload, show an actionable retry state, and never show a false completion message. On success, show a clear confirmation without exposing stored data.
- **Test Scenarios**: all final fields blank; one prompt answered; full feedback; network failure; server write failure; double-click submit; retry after transient failure; successful completion.
- **Tests**: `pytest -q tests/test_api.py tests/e2e/test_review_flow.py`
- **Acceptance criteria**: General feedback is optional, valid submissions produce one confirmation, failures remain recoverable, and duplicate final writes are prevented by the client and submission identity checks.

### 8. Implement locked, lossless JSON Lines persistence

- **Requirements**: R9, R10, R11, R12
- **Files**: `app/storage.py`, `app/submissions.py`, `tests/test_storage.py`, `data/responses/.gitkeep`, `.gitignore`
- **Details**: Write one UTF-8 JSON object per completed submission to a configurable POSIX response path outside the static web directory. Include a generated submission ID, normalized tester email, server-side submitted timestamp, session start timestamp when available, source repository/ref/commit/version and hashes, ordered review-point records with section/type/judgment/comment, and structured general feedback. Validate the complete object before writing. Use an exclusive file lock, append mode, flush, and fsync so concurrent writes on the intended single host cannot interleave. Fail loudly if the directory is unavailable or the write fails; never fall back to stdout, a temporary file, or an alternate path. Keep response files and `.env` files ignored by Git.
- **Test Scenarios**: one valid append; comments with quotes, Unicode, and newlines; blank optional fields; concurrent append attempts; unwritable path; interrupted write simulation; invalid object; duplicate submission ID.
- **Tests**: `pytest -q tests/test_storage.py`
- **Acceptance criteria**: Each valid completion creates exactly one parseable JSON object on one line, no invalid payload is written, and storage failures are surfaced to the caller.

## Phase 4: Verification, documentation, and pilot readiness

### 9. Add unit, integration, and browser-level test coverage

- **Requirements**: R1, R3, R5, R6, R7, R8, R9, R10
- **Files**: `tests/conftest.py`, `tests/test_source_import.py`, `tests/test_survey_manifest.py`, `tests/test_access.py`, `tests/test_api.py`, `tests/test_storage.py`, `tests/test_workflow.py`, `tests/e2e/test_review_flow.py`
- **Details**: Use pytest with isolated temporary response paths and deterministic test fixtures. Cover source and manifest fidelity, allowlist normalization, protected routes, schema rejection, all review-point ordering, optional text, general feedback, JSONL serialization, write errors, and one complete browser path. Use Playwright for the browser test and exercise desktop and mobile viewport configurations. Tests must not use real tester submissions or write into the production response path.
- **Test Scenarios**: happy path; boundary and malformed input; rejected access; source drift; persistence failure; keyboard navigation; mobile layout; duplicate submission.
- **Tests**: `pytest -q`.
- **Acceptance criteria**: The full suite passes from a clean environment and every requirement with executable behavior has a corresponding test.

### 10. Document setup, provenance, storage, and deployment limits

- **Requirements**: R1, R3, R9, R10, R11, R12
- **Files**: `README.md`, `data/README.md`, `.env.example`, `.gitignore`, `requirements.txt`, `requirements-dev.txt`
- **Details**: Document Python setup, dependency installation, manifest import, required environment variables, local run command, test commands, response-file location, backup expectations, source vintage and hashes, the six-email allowlist, the fact that allowlist entry is not authentication, and the single-instance/POSIX storage assumption. State clearly that the app collects design feedback rather than survey answers and list the out-of-scope features. Do not include real response data or secrets in examples.
- **Test Scenarios**: a new developer follows the README from a clean checkout; missing environment variables produce the documented error; ignored response files do not appear in Git status.
- **Tests**: `python -m compileall app scripts` and a clean-checkout setup smoke test.
- **Acceptance criteria**: Another developer can run the app and its tests without rediscovering source provenance, storage assumptions, or pilot access limitations.

### 11. Run final desktop/mobile pilot smoke checks

- **Requirements**: R2, R4, R5, R6, R7, R8, R10, R11
- **Files**: `tests/e2e/test_review_flow.py`, `README.md`
- **Details**: Run the complete automated suite and manually inspect the flow at a desktop viewport and a narrow mobile viewport. Confirm that exact question text is readable, no controls overlap, progress remains stable, keyboard focus is visible, all required judgments can be selected quickly, optional fields never block, and completion is only shown after a successful write. Verify that a test submission appears as one parseable JSONL line in a disposable response file, then remove the disposable data.
- **Test Scenarios**: full six-email gate smoke; complete review; omitted comments; final prompts; mobile navigation; storage failure recovery.
- **Tests**: `pytest -q`, `python -m compileall app scripts`, and documented browser smoke procedure.
- **Acceptance criteria**: The application is ready for the six named testers with no known blocking usability, source-fidelity, access, or persistence defect.

## Testing Strategy

- **Source integrity**: Pin the upstream commit and validate local source hashes, version, expected IDs, and order before the app starts using the manifest.
- **Domain validation**: Use Pydantic models and manifest-derived expected IDs to reject incomplete or fabricated feedback payloads before persistence.
- **Access control**: Test normalization, allowlist membership, signed session behavior, protected routes, missing configuration, and explicit rejection messages.
- **Persistence**: Test parseability, escaping, locking, fsync/append behavior, invalid payload rejection, unwritable paths, and duplicate submission protection using temporary files.
- **Workflow integration**: Exercise the complete ordered flow with FastAPI's test client and verify that the client never submits underlying survey answer values.
- **Browser usability**: Use Playwright at desktop and mobile viewports for keyboard navigation, visible progress, back/next state, optional text, error recovery, and final confirmation.
- **Manual acceptance**: Inspect typography, contrast, focus, readable long question text, stable control dimensions, and absence of overlap at representative viewport sizes.

## Documentation Checklist

- [ ] Add local setup and run instructions to `README.md`.
- [ ] Record the upstream repository, branch, commit, source paths, version, retrieval date, and hashes.
- [ ] Document the survey review-point sequence and why the app does not collect underlying survey answers.
- [ ] Document the six-email allowlist and explicitly state that it is not authentication.
- [ ] Document `APP_SESSION_SECRET`, `RESPONSE_PATH`, `SURVEY_MANIFEST_PATH`, and secure-cookie deployment settings.
- [ ] Document JSONL schema, file permissions, backup expectations, and single-instance/POSIX locking assumptions.
- [ ] Document test commands, browser setup, and the desktop/mobile smoke procedure.
- [ ] Keep `.env`, response files, and disposable test output out of version control.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Upstream draft changes after the plan's recorded commit. | Testers review wording that is not auditable or no longer matches the intended draft. | Pin commit and hashes, retain source artifacts, validate manifest, and require an explicit source-vintage update before changing data. |
| Allowlist-only access is spoofable. | An unauthorized person who knows an approved email could submit feedback. | Restrict the pilot URL and data exposure, state the limitation in the UI and docs, and treat SSO or magic links as a future security change. |
| Flat-file storage is unavailable or the host filesystem is ephemeral. | Completed feedback is lost or falsely reported as saved. | Require a configured response path, fail loudly, lock/flush/fsync writes, test write failures, and document backup and single-host deployment assumptions. |
| Browser interruption before final submission loses in-progress feedback. | A tester must repeat work. | Preserve in-session state in `sessionStorage`, warn that the flow is single-pass, and keep resume-later/server drafts out of scope. |
| Source parsing omits a question or instruction. | The app silently fails the exact-coverage requirement. | Use explicit expected review IDs, source anchors, order checks, manifest hashes, and a test that fails on omissions or duplicates. |
| Long wording or small controls slow testers down. | Low-quality or incomplete feedback. | Use one card at a time, large labeled radio controls, clear progress, keyboard focus, responsive layout, optional text, and browser-level smoke checks. |
| Double submission creates duplicate records. | Feedback counts and downstream review become ambiguous. | Generate a submission ID, validate idempotence on the server, disable submit while pending, and show completion only after one successful write. |

## Out of Scope

- Collecting the underlying NSO answers to G1, G2, or Q1-Q12.
- Calculating survey scores, maturity levels, rankings, or analytics.
- An admin dashboard, response browser, export UI, or survey editor.
- Resume-later support or server-side drafts.
- Multi-instance or managed database storage.
- World Bank SSO, email magic links, passwords, or other strong authentication.
- Changing, paraphrasing, translating, or dynamically fetching the source survey at runtime.

## Completion Contract

### Outcome

A runnable FastAPI application will let only the six approved pilot email identifiers enter, review the pinned global survey in source order, select one required judgment per review point, optionally add comments, submit general feedback, and produce one lossless JSON Lines record per completed session. The app will not collect survey answers, calculate scores, expose an editor/dashboard, or claim strong authentication.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|---|---:|---|---|---|
| V1 | 1 | Pinned source copy and manifest preserve the draft vintage, ordering, IDs, wording, response options, G2 parts, product-reference instruction, and optional evidence guidance. | `pytest -q tests/test_source_import.py tests/test_survey_manifest.py` | yes |
| V2 | 2 | Email normalization accepts only the six approved addresses and rejects every other address; required session configuration fails loudly when absent. | `pytest -q tests/test_access.py` | yes |
| V3 | 3 | The workflow exposes the introduction, gateway, scored items, shared instructions, progress, back/next behavior, and completion only after all required judgments are present. | `pytest -q tests/test_api.py tests/test_workflow.py` | yes |
| V4 | 3 | Invalid IDs, duplicate answers, missing judgments, and invalid labels are rejected; valid optional comments and final feedback serialize without loss. | `pytest -q tests/test_storage.py tests/test_api.py` | yes |
| V5 | 4 | A browser-level happy path works at desktop and mobile widths, including keyboard selection, optional text omission, final submission, and completion confirmation. | `pytest -q tests/e2e` | yes |
| V6 | final | The full test suite, compile check, setup documentation, and disposable storage smoke check pass. | `pytest -q`, `python -m compileall app scripts`, `README.md` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|---|---:|---|---|
| C1 | 1 | Current draft survey wording and order are authoritative. | Manifest/source hash tests and recorded upstream SHA. |
| C2 | 2 | Access is limited to the six configured email identifiers. | Allowlist and protected-route tests. |
| C3 | 3 | Completed responses are precise, lossless, and append safely to JSONL. | Schema, escaping, locking, write-error, and parseability tests. |
| C4 | 2-4 | The pilot remains single-pass and single-instance unless explicitly changed. | Documentation and scope review. |
| C5 | 3-4 | No response data, secrets, or local environment files are committed. | `.gitignore`, disposable-output check, and repository status review. |

### Boundaries

- Allowed: pinned local survey data, FastAPI, minimal accessible HTML/CSS/vanilla JavaScript, signed pilot session cookies, browser session storage for accidental refreshes, JSON Lines persistence, and focused tests.
- Out of scope: underlying NSO survey answers, scoring, analytics, admin dashboard, survey editor, resume-later workflow, multi-instance storage, and SSO/magic-link authentication.

### Iteration Policy

1. Preserve the pinned source and brainstorm requirements as the governing contract.
2. Implement and validate one phase at a time before widening scope.
3. If the source layout or wording differs from the recorded vintage, stop and ask before changing the manifest contract.
4. If a focused test fails, repair that phase and rerun its focused command before proceeding.
5. Treat stronger authentication or managed storage as a separately approved future change.
6. Under `deviation-policy: ask`, pause before any change to requirements, source vintage, storage model, or protected scope and record the decision.

### Blocked-Stop Conditions

- The pinned source commit cannot be retrieved or its content cannot be reconciled with the manifest.
- The app cannot guarantee lossless response writes or cannot establish a documented response-storage path.
- The requested pilot requires real authentication rather than an allowlist identifier check.
- Required dependencies or browser verification cannot run in the target environment.
- A required verification command fails after local repair attempts.
- A required protected boundary must be crossed to continue.
- The execution report cannot be durably created or updated by `/cg-work`.
