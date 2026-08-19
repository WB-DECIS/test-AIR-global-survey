---
date: 2026-08-19
title: "Global survey question-testing application"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "FastAPI question-review flow with pinned local survey data and JSON Lines response storage"
tags: [global-survey, cognitive-testing, feedback-capture, fastapi, jsonl, allowlist]
---
<!-- Created: 2026-08-19 -->

# Global Survey Question-Testing Application

## Context

The project needs a full working application for a controlled pilot of the AI-readiness global survey. The six named World Bank testers should be able to move quickly through the complete draft instrument and give structured feedback on every survey item. The app is for reviewing the survey design, not for collecting the underlying NSO survey answers.

The source survey is maintained in the `research/global-nso-ai-readiness-survey` branch of `zander-prinsloo/AI-Readiness-of-NSOs`, under `global-survey/instrument/global-nso-ai-readiness-survey-draft.md`. The source branch also provides the global-survey README, response-code contracts, and cognitive-testing materials. The source branch head observed during this brainstorm was `fa031bae8ac7f85a88bc989846944b6363cf03e3`.

## Requirements

- Restrict the pilot entry gate to these approved email addresses, case-insensitively:
  - `gcarletto@worldbank.org` (Gero Carletto)
  - `asolatorio@worldbank.org`
  - `zprinsloo@worldbank.org`
  - `userajuddin@worldbank.org`
  - `dmahler@worldbank.org`
  - `hdang@worldbank.org`
- Use a low-friction email allowlist gate. This is an identifier check, not strong authentication, and must be treated as suitable only for a controlled low-risk pilot.
- Present a short introduction explaining that testers are reviewing the global survey, what the survey is for, and that responses are recorded for feedback.
- Use the exact current draft question text and structure from a versioned local copy or manifest. Record the source ref/vintage with each submission so tested wording is auditable.
- Walk testers through the full instrument in order, starting with Gateway questions G1 and G2 and continuing through scored questions Q1-Q12, including the Q8-Q11 product-reference instruction and optional evidence guidance where it is part of the draft.
- At each review point require one quick judgment: `Good question`, `Bad question`, or `Needs refinement`.
- Make written comments optional. Testers must be able to continue without typing text.
- Provide one optional feedback field alongside each question or review point.
- Provide a final general-feedback page with prompts such as missing questions, survey length, confusing sections, and other recommendations.
- Keep the workflow single-pass for the pilot. Resume, scoring, analytics, an admin dashboard, and an in-app survey editor are out of scope.
- Store each submission precisely, including tester email, timestamps, survey vintage/source commit, question or review-point ID, section, selected judgment, optional comment, and final general feedback.
- Optimize for speed and ease of use: one clear review card at a time, visible progress, large keyboard-friendly choices, explicit next/back controls, and a clear completion confirmation.
- Use flat-file storage for the pilot, preferring JSON Lines because each submission contains nested per-question records and must remain lossless and easy to inspect.

## Approaches Considered

### Approach 1: FastAPI question-review flow with pinned local survey data and JSON Lines storage

Build a small Python web application with a server-rendered or minimal client-side review interface. Import and normalize the source draft into a checked-in local survey manifest while preserving the original source document and source metadata. Render the gateway and scored sections in source order, collect one judgment per review point, append one complete JSON record per submission, and expose no dashboard or analytics.

Pros: few moving parts, fast interaction, precise nested records, straightforward local execution, and a clean path to a single hosted instance. It directly supports the charter's exact-text and precise-storage requirements.

Cons: an email allowlist is not authentication; flat-file persistence needs a single-instance deployment assumption and safe append handling; moving to multiple app instances later would require a database or managed storage service.

Effort: medium.

Recommended: yes. It matches the pilot's narrow scope and prioritizes tester usability without introducing unnecessary product surface.

### Approach 2: Streamlit app with CSV export

Build the review flow in Streamlit and write a flat CSV export after final submission.

Pros: small implementation and quick deployment; CSV is immediately inspectable.

Cons: less control over question-by-question navigation and keyboard flow, more awkward preservation of nested comments and source metadata, and more potential for accidental state loss or inconsistent partial submissions.

Effort: small to medium.

Recommended: no. It optimizes build speed at the expense of the frictionless tester experience and lossless record structure.

### Approach 3: React/Vite frontend with API backend and SQLite

Build a dedicated frontend and API, store structured submissions in SQLite, and leave room for future resume or administration features.

Pros: strongest interaction design and validation control, reliable concurrent persistence, and a good foundation if this evolves into a broader service.

Cons: substantially more dependencies and deployment surface than this pilot needs, and SQLite moves away from the selected flat-file storage preference.

Effort: large.

Recommended: no for this iteration. Reconsider if the pilot becomes a recurring or multi-instance production workflow.

## Decision

Choose Approach 1: a FastAPI question-review application with a pinned local survey manifest and JSON Lines response storage.

The app will treat the draft survey as immutable test input for each build. The application will not ask testers to answer G1-G2 or Q1-Q12; it will display the exact survey content and collect design feedback about each review point. The required judgment is the only required action. Optional text fields are available for precise suggestions but never block progress.

The allowlist-only gate is a deliberate pilot trade-off for ease of access. It must be documented as non-authenticating and should only be used where the URL and collected feedback are considered low risk. A future deployment requiring stronger confidentiality should replace it with World Bank SSO or email magic links.

## Next Steps

1. Copy the draft instrument and relevant source metadata into this repository, pinned to the source branch and commit recorded above.
2. Build a structured survey manifest that preserves section order, question IDs, exact wording, response options, gateway parts, product-reference instructions, and optional evidence guidance.
3. Implement the approved-email entry gate, introduction page, sequential review cards, progress indicator, back/next navigation, optional comments, final general-feedback prompts, and completion confirmation.
4. Implement lossless JSON Lines submission storage with safe append behavior and explicit errors for failed writes.
5. Add focused tests for source-manifest integrity, allowlist behavior, required judgments, optional text, full-flow ordering, and response serialization.
6. Document local setup, the flat-file storage location, the source survey vintage, the allowlist limitation, and the eventual deployment assumptions.
7. Validate the complete flow at desktop and mobile widths before handoff to the six testers.
