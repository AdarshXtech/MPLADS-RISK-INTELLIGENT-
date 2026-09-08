# Application execution flow

This document describes the implementation that exists in the repository on 2026-09-08. It does not describe planned behaviour as if it were implemented.

## Current implementation status

The repository contains a Next.js data-readiness command centre, an authenticated Investigation Queue, FastAPI aggregate and review endpoints, standalone inspection/ingestion commands, a deterministic detector command and a read-only human-review CSV export command. One potential-duplicate candidate rule is active. PostgreSQL staging, detector persistence and append-only review history are verified against the project-local PostgreSQL 17.11 service. Composite scores and project profiles remain unimplemented.

## Continuous integration flow

The frontend lockfile was reconciled with npm 10 after a locally reproduced clean-install validation failure. Both npm 10 and npm 11 accept the repaired graph. CI continues to use the committed lock through `npm ci`; application request flow is unchanged.

```text
push or pull request to master, or manual run
-> GitHub Actions CI
-> Backend: pinned uv + Python 3.12 -> locked sync -> Ruff -> Pytest -> ephemeral PostgreSQL 17
-> Frontend: Node.js 22 -> npm ci -> ESLint -> Playwright production build -> Chromium + Firefox + WebKit
```

The two jobs run independently with `contents: read`. They consume no official source files and perform no deployment. Browser tests use the existing clearly synthetic mock API and runtime-generated test credentials.

## Frontend entry point

### Responsive presentation and screenshot flow

The shared `globals.css` wraps narrow navigation and headers, adapts metric/filter grids to available width, swaps source tables for existing cards in narrow analysis columns and wraps long evidence. The shared skip link receives keyboard focus explicitly and targets a programmatically focusable main element in Command Centre, queue and evidence pages. No API or detector flow changes.

`e2e/responsiveness.spec.ts` -> authenticated loopback mock scenario configuration -> actual Next.js pages -> viewport/control bounds assertions -> optional labelled PNG capture with `CAPTURE_UI=1`. `node e2e/build-gallery.mjs` reads these images and generates the local browser/size-filtered gallery. Loading, empty, failure and review transition fixtures never reach official PostgreSQL.

Session files: shared CSS; mock API; responsive spec; gallery generator; `docs/responsive-ui.md`, feature connections, decisions, flow, techstack, deployment and CODEX_LOG.

### Filtered queue export

`ExportButton` receives the applied query/state/status filters without pagination. It requests `GET /investigation-queue/export`; that Next.js route verifies the signed session and calls `getCandidateCsv()`. The server-only client sends the review API key to FastAPI `GET /investigation-candidates.csv`. After validating the key and inputs, `export_candidates()` shares `candidate_filter()` and the queue selected-run query. One PostgreSQL statement reads matching candidates and latest review details. More than 10,000 groups is refused; otherwise `encode_csv()` writes formula-safe CSV with provenance and rule/run identity. A private/no-store response becomes the browser download. Empty results produce headers only; expired sessions return 401; upstream failures offer retry/narrow-filters guidance. No records or flags are changed.

Continuation files: backend investigations, main, review_export and investigation tests; frontend queue page, export route/button, investigations client, global CSS and E2E mock/tests; PRD, architecture, techstack, feature-connections, investigation-queue guide, decisions, flow and CODEX_LOG. Source-card CSS was corrected without changing evidence.

### Queue sorting

The queue validates its `sort` search parameter against four displayed choices and defaults unknown values to `group_smallest`. It forwards the selected value with filters to FastAPI. FastAPI validates the same value as a closed enum. `list_candidates()` selects its ORDER BY expression only from `SORT_SQL`, then PostgreSQL orders the full matching set before LIMIT/OFFSET. Result ID breaks ties, so page movement is stable. The sort value is preserved by pagination and forwarded to `export_candidates()`, which applies the same order to all exported matches. Sorting performs no write and cannot affect a detector result or review event.

### Command centre

1. `frontend/app/layout.tsx` defines `RootLayout`, metadata and the `en-IN` document language.
2. `frontend/app/page.tsx` redirects `/` to `/command-centre`.
3. `CommandCentrePage` calls `requireReviewer()`; unauthenticated requests redirect to `/login`.
4. It requests public ingestion aggregates from `GET /data-overview` and protected queue counts from `GET /investigation-summary` in parallel. The API key remains server-side.
5. `investigation_summary()` selects the latest reviewable run and counts each candidate by its latest append-only event; no event means New.
6. Valid responses render real workload and ingestion metrics in the shared reviewer shell. A failed, timed-out or invalid request renders the service-error state and working retry link.
7. `loading.tsx` supplies the route loading presentation. Desktop uses accessible tables and analysis rails; phones use labelled cards and stacked content.

`/login` validates configured reviewer credentials in a Server Action and sets an eight-hour HTTP-only signed cookie. `/investigation-queue` revalidates the session server-side, applies server-side search, State/status filters and pagination, and requests a bounded candidate page from FastAPI. `/investigation-queue/[id]` loads detector evidence, matched source records, provenance and review history. Its Server Action revalidates the session before posting a permitted status transition.

Current call relationship:

```text
GET /
-> Home()
-> redirect /command-centre
-> CommandCentrePage()
-> getOverview()
-> GET FastAPI /data-overview
-> runtime response validation
-> Dashboard(data) or service-error state
```

No browser-side JavaScript receives the database connection string. The server-rendered route calls FastAPI from the Next.js process.

## Backend entry point

`backend/src/backend/main.py` creates the FastAPI application object `app`.

The separate `backend` console script maps to `backend.__init__.main()` and only prints a greeting. It does not launch the API server.

Implemented request flows:

```text
GET /
-> backend.main.root()
-> FastAPI serialises {status, service}
-> HTTP 200 JSON response

GET /health
-> backend.main.health()
-> FastAPI serialises {status}
-> HTTP 200 JSON response

GET /data-overview
-> backend.main.database_connection()
-> Psycopg read-only application connection
-> backend.main.read_data_overview()
-> grouped query over staging batch/record tables
-> Pydantic DataOverview response
-> HTTP 200 JSON response, or generic HTTP 503 when unavailable

GET /investigation-summary
-> require_review_key()
-> database_connection()
-> investigations.investigation_summary()
-> latest reviewable run plus latest append-only status
-> protected aggregate status counts

GET /investigation-candidates
-> require_review_key()
-> database_connection()
-> investigations.list_candidates()
-> latest reviewable run plus latest review event
-> filtered, paginated CandidatePage

GET /investigation-candidates.csv
-> require_review_key()
-> investigations.export_candidates()
-> same filters and whitelisted sort as queue, without pagination
-> formula-safe CSV response

GET /investigation-candidates/{result_id}
-> require_review_key()
-> investigations.candidate_detail()
-> detector evidence, source provenance and review history

POST /investigation-candidates/{result_id}/events
-> require_review_key() and reviewer header validation
-> investigations.add_review_event()
-> validate transition and mandatory final fields
-> transaction lock and current-status check
-> append one immutable review event
```

There is no speculative repository or service abstraction. The narrow review query and transition functions live in `backend.investigations`.

## API flow

The two status routes, aggregate data-overview route and four protected investigation routes exist. No composite-risk or project-profile API exists.

## Authentication flow

The frontend uses one environment-configured reviewer account. A successful login creates an HMAC-signed, HTTP-only, SameSite Lax cookie. The Command Centre, queue, candidate pages and every Server Action call `requireReviewer()`. Next.js adds the review API key and authenticated reviewer identity only to server-to-server FastAPI requests. This local authentication must be replaced by the approved organisational identity provider before production.

## Data ingestion flow

`backend.inspect_exports.run()` inventories raw files, calls `ingest()` / `inspect_csv()` for CSV, calls `xlsx_audit()` -> `read_static_xlsx()` for independent Excel comparison, calculates ID-set overlaps and writes inspection output and the measured dictionary. PDF is reference only.

`python -m backend.ingest` -> `main()` -> `ingest()` -> `inspect_csv()` -> `clean_value()` / `money()` -> separate original/cleaned/derived rows and validation issues -> versioned `report.json` and `records.jsonl`. Raw sources remain untouched. Exact reruns compare bytes; inconsistent existing outputs are refused. Summary and malformed-width rows are retained separately from details. No ingestion function invokes a detector or the API.

## Detector execution order

`python -m backend.detectors` -> `main()` reads DATABASE_URL -> `load_inputs()` reads ordered source-batch identities and sanctioned detail records -> `build_run()` -> `detect()` -> `duplicate_work_candidates()` -> `stage_run()` transaction.

The rule normalises configured text without modifying source values, groups records by seven required descriptive/administrative/date/amount fields, requires distinct Work IDs, and emits one explainable review candidate per group. Result IDs and run IDs are content-derived. An identical rerun verifies metadata and result count without reinsertion. Unsupported detectors and their missing inputs are stored in run metadata.

`peer_cost_candidates()` exists for tested calibration only and is disabled in the reviewable engine configuration. Data-quality validation remains an ingestion result and is not converted into a risk candidate.

## Human-review export flow

`python -m backend.review_export --output <path>` -> select the latest reviewable detector run -> load its duplicate-work candidate results -> load matching staged sanctioned records -> enrich exact Work IDs from staged recommended records -> `build_rows()` -> `encode_csv()` -> `write_once()`.

The export contains one row per candidate group, sorted from the smallest group to the largest. Detector evidence, match basis, limitations and source-record references are populated. Decision, reason, documents, reviewer and notes fields remain blank for human input. CSV values that could be interpreted as spreadsheet formulas are neutralised. An identical rerun is accepted, but changed content cannot overwrite an existing path. The command performs no database write and does not change detector results.

## Risk aggregation flow

Not implemented. No composite risk score is calculated or displayed. Detector severity is `review`; confidence means deterministic predicate certainty, not likelihood of misuse.

## Database persistence flow

`python -m backend.staging` -> `main()` reads DATABASE_URL -> `inspect_csv()` -> `psycopg.connect()` transaction -> optional explicit table creation -> `stage()` -> parameterised batch/record inserts. Source hash, parser version and row ordinal identify records, not Work ID. Original/cleaned/derived/issues are separate JSONB fields. Repeated batches are checked, not reinserted. Exceptions roll back the transaction.

`mplads_detector_run` stores immutable configuration, sources, unavailable detectors, result count/hash and run disposition. `mplads_detector_result` stores explainable candidate evidence and source references. The version-1 calibration run is retained. The latest version-2 reviewable run is tied to all six source batches and contains 174 potential-duplicate groups. The application role has SELECT/INSERT but no UPDATE/DELETE permission on detector tables. The development database contains six source batches and 141,717 retained source records; see `docs/ingestion.md`.

`mplads_review_event` stores append-only transitions, decisions, reasons, documents checked, evidence references, notes, reviewer identity and timestamp. `NEW` is implicit before the first event. Current state is derived from the newest event, so no event or detector row is overwritten. The application role has SELECT/INSERT and no UPDATE permission on this table.

## Files changed in the current session

- `.github/workflows/ci.yml`
- `frontend/package-lock.json`
- `docs/deployment.md`
- `docs/decisions.md`
- `docs/flow.md`
- `docs/techstack.md`
- `docs/CODEX_LOG.md`

The earlier implementation inventory follows for historical context:

- `.gitignore`, `.env.example`
- `scripts/postgres.ps1`
- `backend/src/backend/main.py`, `backend/tests/test_main.py`
- `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/globals.css`
- `frontend/app/command-centre/page.tsx`, `frontend/app/command-centre/loading.tsx`
- `frontend/next.config.ts`
- `docs/feature-connections.md`
- `backend/pyproject.toml`, `backend/uv.lock`
- `backend/src/backend/ingest.py`, `backend/src/backend/inspect_exports.py`, `backend/src/backend/staging.py`
- `backend/src/backend/detectors.py`
- `backend/src/backend/review_export.py`
- `backend/src/backend/investigations.py`, `backend/tests/test_investigations.py`
- `frontend/lib/auth.ts`, `frontend/lib/investigations.ts`
- `frontend/app/login/`, `frontend/app/investigation-queue/`
- `frontend/e2e/`, `frontend/playwright.config.ts`, frontend package files
- `backend/tests/test_ingest.py`, `backend/tests/test_inspect_exports.py`, `backend/tests/test_staging.py`, `backend/tests/test_detectors.py`, `backend/tests/test_review_export.py`
- `docs/ingestion.md`

- `docs/PRD.md`
- `docs/techstack.md`
- `docs/architecture.md`
- `docs/data-dictionary.md`
- `docs/detection-rules.md`
- `docs/source-register.md`
- `docs/decisions.md`
- `docs/flow.md`
- `docs/CODEX_LOG.md`

Twelve raw copies and generated outputs exist under Git-ignored `data/`. The generated review CSV also remains Git-ignored under `data/review/`. `Works Recommended.csv` flows through parser version 2, PostgreSQL staging, detector source-batch identity and review-export enrichment. The authenticated queue exposes only the latest reviewable detector results and their linked source evidence. Detection remains a separate deterministic backend path, reviewer actions cannot change flags, and no composite score was created.
