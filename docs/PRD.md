# Product requirements

Status: requirements baseline with verified ingestion, one deterministic candidate rule, a data-readiness command centre and the first authenticated Investigation Queue slice. Updated 2026-09-07.

## Purpose and users

SIH26102 is the project identifier supplied by the team. The official statement still requires verification; see [source register](source-register.md). Build an MPLADS administrative decision-support layer for MoSPI, State Nodal Authorities, District Authorities and MPs. The primary workflow is a ranked investigation queue, not a decorative dashboard.

Every alert must answer what is unusual, its severity, why it was flagged, the supporting source evidence and what an official should verify first. An anomaly does not prove fraud. All numerical examples in the supplied brief are illustrative requirements, not observations or target detection counts.

## Required capabilities, not yet implemented

1. Immutable official input, measured field inventory, validation reports, separate cleaned values and source-row provenance.
2. Only data-supported deterministic/statistical detectors; conventional ML only when useful and verifiable. Document unavailable detectors and missing inputs.
3. Explainable 0 to 100 risk contributions, configurable Critical/High/Medium/Low thresholds and separate data confidence. Missing evidence must not silently become a Low score.
4. Investigation queue with server-side search, state/status filtering, four safe sorting choices, pagination and authenticated all-matching-results CSV export. These capabilities are implemented. See [queue usage](investigation-queue.md).
5. Project risk profile with evidence, source record, peer rationale, timeline, candidate duplicates, available compliance checks and verification guidance.
6. Persistent cases: New, Under Review, Verification Requested, Resolved and Dismissed; notes, mandatory dismissal reason, reopening and retained history. These statuses, transitions and append-only history are implemented for one local reviewer role. Assignment and production identity integration remain unimplemented.
7. Supporting command centre, peer analysis, rules/model audit and data quality/source pages. Display trends only when actual comparable dated observations exist.

Generative AI may optionally explain already computed evidence. It must never create or modify flags, confidence or scores. Detection must work without it. No agent framework, invented official records, fake live data or non-working controls.

## Acceptance criteria

- Every score exposes its contributions, inputs, provenance, version and limitations.
- Every implemented control has a repeatable E2E test or explicit manual QA record. State-changing actions persist and have error handling.
- Loading, empty, unavailable, success, error and retry states are tested where applicable.
- Responsive phone, tablet, laptop and desktop layouts; no overlap or horizontal overflow; usable at 200% zoom. Semantic HTML, labels, visible focus, keyboard navigation, sufficient contrast and reduced motion.
- Chromium, Firefox and WebKit coverage where practical, with failures or omissions reported explicitly. Use axe where practical.
- Paginated results, bounded client payloads and measured performance on constrained devices/network. No performance claims without measurements.
- Synthetic fixtures stay in automated tests, never in official product demonstrations.
- Indian English, no emojis or em dashes, and no claims that fraud is proven.

## Phase gates

Follow the latest brief: Phase 0 repository/research; 1 dataset analysis/documentation; 2 database/ingestion; 3 deterministic rules; 4 statistical engine; 5 risk/explanations; 6 API; 7 investigation workflow; 8 UI; 9 accessibility/responsiveness; 10 browser QA; 11 performance; 12 demo verification.

Phase 0 is partial. Field inspection, file ingestion and PostgreSQL staging now cover all six supplied CSV report sets, and the live database integration test passes. The recorded export scope is All India, Lok Sabha. Source completeness, exact extraction time, allocation period, calamity scope and human review remain unresolved. Do not build risk UI to bypass these gates. The earlier session's label "Phase 2 dataset inspection" remains historical; this document uses the latest phase numbering.

## Current implementation

The Next.js root redirects to an authenticated, server-rendered Command Centre backed by FastAPI and PostgreSQL. It shows real queue workload by append-only review status alongside ingestion readiness. A separate authenticated Data Quality page presents source-level ingestion and validation evidence with explicit coverage limits. The backend persists one active deterministic potential-duplicate candidate rule, which produced 174 reviewable groups from the supplied sanctioned-work snapshot. These are verification candidates, not duplicate findings. The queue supports server-side search, state/status filters, sorting, pagination, filtered CSV, evidence/provenance inspection and append-only review transitions. A peer-cost rule remains disabled because its 3,016 calibration candidates were too broad. No composite score or project dossier exists. See [feature connections](feature-connections.md), [actual flow](flow.md), [deployment readiness](deployment.md), [detector rules](detection-rules.md), [data inventory](data-dictionary.md) and [ingestion instructions](ingestion.md).
