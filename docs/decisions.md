# Technical decisions

## 2026-09-09: Deploy frontend to Cloudflare and backend with PostgreSQL to Render

- **Problem:** The staging demonstration requires a live deployment environment with secure separation between public web traffic, administrative backend services, and database storage, without incurring unnecessary cloud hosting costs or fabricating missing data.
- **Decision:** Deploy the Next.js 16 frontend to Cloudflare Workers / Pages using the `@opennextjs/cloudflare` adapter with `nodejs_compat`. Deploy the FastAPI backend and managed PostgreSQL database to Render using Blueprint specification (`render.yaml`). Provide an idempotent schema initialisation script `backend/src/backend/init_db.py`.
- **Alternatives considered:** Deploy all tiers on Render (exceeds free single web service tier); deploy backend on Cloudflare Workers (Cloudflare Workers Wasm/Python environment does not support persistent Uvicorn processes or native Psycopg binary sockets); single-server container deployment (adds VPS management overhead).
- **Library selection:** Added `@opennextjs/cloudflare` and `wrangler` as frontend development dependencies. No runtime dependencies added to the backend; existing standard library, `fastapi`, and `psycopg` are sufficient.
- **Trade-offs:** Render free tier web services spin down after 15 minutes of inactivity; frontend request timeout is set to 45 seconds (`MPLADS_API_TIMEOUT_MS`) to accommodate cold-start latency. Free Render databases have a 30-day retention limit suitable for ephemeral staging.
- **Performance impact:** Frontend achieves global low-latency edge delivery via Cloudflare CDN. Server-to-server HTTPS requests to FastAPI are made only for authenticated reviewer routes.
- **Maintainability impact:** `render.yaml` enables one-click Infrastructure-as-Code recreation on Render. `init_db.py` unifies schema migration across local development, CI, and staging environments.
- **Security impact:** Database credentials and the `X-MPLADS-Review-Key` secret remain strictly server-side. Browser bundles never receive database strings or internal API keys.
- **Affected files:** `render.yaml`, `backend/src/backend/init_db.py`, `backend/tests/test_init_db.py`, `frontend/wrangler.jsonc`, `frontend/open-next.config.ts`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/lib/investigations.ts`, `frontend/app/command-centre/page.tsx`, `docs/cloudflare-render-deployment.md`, `docs/deployment.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.

## 2026-09-08: Repair npm 10 lockfile compatibility

- **Problem:** The first hosted frontend CI failed during `npm ci`. The public annotation only reports exit code 1 and downloading detailed logs returned HTTP 403. Locally, npm 10 reproduces `EUSAGE` with missing `@emnapi/core@1.11.3` and `@emnapi/runtime@1.11.3`; npm 11 had previously accepted the lock.
- **Decision:** Regenerate only lock metadata through npm 10 `install --package-lock-only`, then check both npm 10 and npm 11. Keep the existing Node.js 22 CI target and strict `npm ci` step.
- **Alternatives:** Replace CI with `npm install`, bypass peer checks or switch Node versions. These would hide or avoid the inconsistent dependency metadata rather than repair it.
- **Library selection:** No direct dependency added. npm resolves missing optional WASI dependencies and bundled metadata using the declared dependency graph.
- **Trade-offs:** npm versions serialise some peer metadata differently. Hosted confirmation still requires a new successful run; the inaccessible remote log prevents claiming an exact remote error match.
- **Performance impact:** No intended runtime change; clean install retains optional platform selection.
- **Maintainability impact:** The lock now validates with both package-manager majors tested locally.
- **Security impact:** No credentials, repository settings or data changed.
- **Affected files:** `frontend/package-lock.json`, decisions, flow and session log.

## 2026-09-08: Verify responsive layouts through the existing browser suite

- **Decision:** Repair the shared CSS and extend the existing Playwright suite with eight viewport sizes and three-browser screenshot capture. Use a locally generated HTML gallery for reviewing PNGs.
- **Problem:** Navigation did not wrap on small phones; laptop filter columns had minimum widths exceeding the available workspace; long evidence values and narrow source tables needed safer reflow.
- **Selected approach and reason:** Reuse native grid/flex wrapping, existing mobile cards and the current test API. Delay the six-column filter layout until 1600 pixels, retain fewer metric columns on tablets and expose source cards when the desktop analysis column is narrow.
- **Keyboard finding:** A minimal WebKit reproduction confirmed that its default Tab behaviour skips an implicit anchor tab stop. The shared skip link now has explicit `tabIndex=0` and each shell main-content destination has `tabIndex=-1`. The test verifies both link focus and focus transfer after Enter.
- **Alternatives:** A new component library, a mobile navigation drawer, image-generation mock-ups or changing live official review data. Existing CSS and browser automation cover the requested task.
- **Library selection:** None added. Ponytail favoured existing CSS, Playwright and Node filesystem/path APIs. Installed Next.js CSS documentation and Context7 Playwright documentation were consulted.
- **Trade-offs:** Mobile pages remain vertically scrollable because all evidence stays available. Screenshots use clearly labelled synthetic data. The 640-pixel reflow check approximates 200% zoom without claiming a native zoom test.
- **Performance impact:** No new browser dependency or runtime request. Browser CI runs additional responsive checks; optional screenshots are written only with `CAPTURE_UI=1`.
- **Maintainability impact:** Shared selectors fix all implemented routes. Test-only response controls make loading/error/empty screenshots reproducible without production test switches.
- **Security impact:** No official data, credentials or review events are changed. Scenario controls exist only in the loopback test server and require its generated API key.
- **Affected files:** `frontend/app/globals.css`, shared queue shell and Command Centre/queue/evidence pages, `frontend/e2e/mock-api.mjs`, `frontend/e2e/responsiveness.spec.ts`, `frontend/e2e/build-gallery.mjs`, responsive guide, feature connections, decisions, flow, technology and deployment guides, session log. Generated screenshots remain in ignored `output/responsiveness/`.

## 2026-09-08: Add provider-neutral GitHub Actions verification

- **Status:** Implemented locally; the first hosted run requires a normal push.
- **Problem:** The GitHub baseline exists, but broken backend, database or browser behaviour can still be pushed without an automated check.
- **Decision and reason:** Add one workflow with two independent jobs. The backend runs Ruff and the complete Pytest suite against an ephemeral PostgreSQL 17 service. The frontend runs ESLint and the existing production-build Playwright suite across Chromium, Firefox and WebKit. Trigger it for `master` pushes, pull requests and manual runs.
- **Alternatives considered:** Select and deploy to a cloud provider now; add Dockerfiles; run only unit tests; introduce a CI matrix or dependency-update bot. Those choices are unnecessary before the staging host is selected or would weaken the existing integration and browser coverage.
- **Library selection:** No application library added. GitHub Actions, the official GitHub checkout/setup-node actions and maintained Astral setup-uv action are sufficient. Action revisions and uv are pinned. Context7 and current official GitHub, uv and Playwright guidance were checked. Ponytail kept the workflow to the two existing test boundaries.
- **Trade-offs:** Playwright installs three browsers on each uncached runner and its current configuration rebuilds Next.js, so the frontend job is slower than lint alone. The workflow tests synthetic browser fixtures, not a deployed environment.
- **Performance impact:** No runtime impact. CI has 15-minute backend and 30-minute frontend limits.
- **Maintainability impact:** Existing local commands remain the CI commands. There is no provider-specific deployment logic to maintain.
- **Security impact:** Workflow permission is limited to `contents: read`. No repository secret or official data is used. The PostgreSQL credential is unique to the run and the service is discarded with its isolated runner. The workflow cannot deploy or mutate repository content.
- **Affected files:** `.github/workflows/ci.yml`, `frontend/package-lock.json`, `docs/deployment.md`, `docs/decisions.md`, `docs/flow.md`, `docs/techstack.md`, `docs/CODEX_LOG.md`.

## 2026-09-08: Create and push a secret-audited deployment baseline

- **Status:** Implemented and pushed to `origin/master`.
- **Problem:** The configured GitHub remote has no branch, while the complete project exists only as untracked workstation files.
- **Decision and reason:** Create one reviewed initial commit containing source, tests, reproducible manifests, safe MCP configuration and current documentation, then push it normally to the configured empty GitHub remote. Keep official/raw/processed data, local PostgreSQL state, browser artefacts, environment files and generated output outside Git.
- **Alternatives considered:** Push immediately; commit official datasets; include the outdated generated PDF; add provider-specific containers and CI before choosing the staging host.
- **Library selection:** Not applicable. Git and existing ignore rules are sufficient. Ponytail favoured a provider-neutral baseline.
- **Trade-offs:** The first commit is necessarily larger than normal feature commits because the remote is empty. Generated explanatory output remains local until regenerated from current implementation. Deployment automation is deferred until the target is known.
- **Performance impact:** No runtime impact.
- **Maintainability impact:** Root, backend and frontend READMEs now provide project-specific entry points. Dependency lockfiles and tests are versioned.
- **Security impact:** Candidate files were checked for common private-key, service-token and credential-bearing database URL patterns. Secrets, source exports and database state remain ignored. The push was a normal new-branch push with no force, deletion or repository-setting change.
- **Affected files:** `.gitignore`, root/backend/frontend READMEs, deployment guidance, decisions and session log; the initial commit includes the existing project baseline.

## 2026-09-07: Surface protected queue workload and defer provider-specific deployment files

- **Status:** Implemented and verified for the workload; deployment remains gated.
- **Problem:** Officials need to see how many candidates require action, while the team needs an honest deployment path.
- **Decision and reason:** Add one protected aggregate query for status counts and require the signed reviewer session for the Command Centre. Reuse the existing application shell and show candidate, New, Under review, Verification requested and Closed counts. Document a portable Next.js, FastAPI and PostgreSQL staging shape without selecting a provider or adding speculative infrastructure.
- **Alternatives considered:** Expose candidate counts publicly; calculate counts from paginated browser data; add a chart; add Docker/cloud files before choosing a host; deploy using the local single-account login.
- **Library selection:** None. PostgreSQL filtered aggregates, existing Pydantic/Next.js components and native HTML are sufficient. Context7 and installed Next.js 16 self-hosting documentation were used for deployment boundaries.
- **Trade-offs:** The Command Centre now requires reviewer authentication. If either aggregate endpoint fails, it shows the existing service-unavailable recovery state. The first staging shape is single-instance; scaling controls are deferred until needed.
- **Performance impact:** One aggregate database query over the latest 174 result groups per Command Centre request. No cache or new index was added at this scale. No performance SLA is claimed.
- **Maintainability impact:** The shared shell removes duplicate navigation/session UI. One summary model and query keep status semantics aligned with append-only events.
- **Security impact:** Candidate counts are no longer shown on an unauthenticated page. Backend summary access requires the review API key. Production remains blocked on organisational identity, private TLS PostgreSQL, secret management and operational approval.
- **Affected files:** Backend investigations/main and tests; frontend Command Centre, shared queue shell, investigations client, CSS, E2E mock/tests; deployment and implementation documents.

## 2026-09-07: Use a closed set of queue sort orders

- **Status:** Implemented and verified.
- **Problem:** Reviewers could filter and page through candidates but could not change their administrative review order.
- **Decision and reason:** Add one `sort` query parameter with four useful values: smallest group, largest group, State A to Z and most recently reviewed. PostgreSQL sorts before pagination; result ID is the stable tie-breaker. CSV uses the same order.
- **Alternatives considered:** Client-side sorting would only reorder one page; arbitrary column/direction parameters expand validation and SQL risk; a table library is unnecessary.
- **Library selection:** None. Existing SQL, Next.js GET forms and native select controls are sufficient. Current Next.js documentation confirmed promised page search parameters and query navigation.
- **Trade-offs:** Sorting is limited to fields useful in the current evidence model. There is no amount sort because report units and semantics must not be guessed. Records with no review event appear after reviewed records in the recent order.
- **Performance impact:** Sorting occurs in the existing bounded database query. No performance claim was made and no index was added for 174 current groups.
- **Maintainability impact:** One backend SQL whitelist is the source of allowed clauses. The frontend presents matching values and defaults invalid URL values safely.
- **Security impact:** FastAPI exposes the allowed values as a closed enum; user text is never inserted into an ORDER BY clause. Authentication and database permissions are unchanged.
- **Affected files:** `backend/src/backend/investigations.py`, `backend/src/backend/main.py`, investigation/main tests, queue page, investigations types, export route, CSS, E2E mock/tests, and the project documents listed in the session log.

## 2026-09-07: Export applied Investigation Queue filters

- **Status:** Implemented and verified.
- **Problem:** Reviewers need filtered candidates, including results beyond the visible page, as a portable record.
- **Decision and reason:** Share the queue predicate, use one read-only PostgreSQL snapshot and reuse the standard-library CSV encoder. Preserve source references, detector/run identity and latest review details. Search treats SQL wildcard characters literally.
- **Alternatives considered:** Current-page browser export omits records; repeated paginated requests can mix snapshots; new libraries/background jobs are unnecessary at current scale.
- **Library selection:** None added. Existing Python csv/json and native Next.js/browser APIs suffice. Context7 and installed Next.js documentation informed the authenticated route.
- **Trade-offs:** Latest review details only, not full history. More than 10,000 groups is rejected without truncation. Upstream failures produce a generic retry/narrow-filters message.
- **Performance impact:** Bounded in-memory export; current 174 groups produce 489,951 bytes. No performance SLA claimed.
- **Maintainability impact:** Shared filters and formula neutralisation avoid divergent logic. A specific CSS selector restores desktop source-card visibility.
- **Security impact:** Signed session and server-side API key required; private/no-store responses and formula-safe CSV. No new permissions or database mutation. Downloaded evidence and notes require secure handling.
- **Affected files:** Backend investigations, main, review_export and investigation tests; frontend queue page, export route/button, investigations client, global CSS and E2E fixtures/tests; PRD, architecture, techstack, feature connections, queue guide, decisions, flow and CODEX_LOG.

## 2026-09-07: Start the Investigation Queue with append-only review events

- **Status:** Implemented and verified.
- **Decision:** Expose the latest reviewable potential-duplicate run through authenticated FastAPI endpoints and a server-rendered Next.js queue. Use one locally configured reviewer account, an HTTP-only signed session cookie, a separate server-to-server API key, and an append-only PostgreSQL event table. Define and enforce New, Under Review, Verification Requested, Resolved and Dismissed transitions. Require a decision for resolution or dismissal and a reason for dismissal.
- **Problem:** The 174 real candidate groups had a CSV review aid but no secure product workflow for searching evidence, inspecting provenance or retaining review history.
- **Alternatives:** Edit detector rows, add a full identity provider, use browser-side API credentials, or build the complete case-management scope immediately. These would break auditability, assume unavailable infrastructure, expose secrets or expand the feature beyond a complete first slice.
- **Selected approach and libraries:** Use existing FastAPI, Pydantic, Psycopg and PostgreSQL advisory locks. Use Next.js Server Components, Server Actions, native Node cryptography and signed cookies. Add only the project-required `@playwright/test` development package. Ponytail kept the slice to one reviewer role, one append-only table and native platform features.
- **Trade-offs:** Local single-account authentication is suitable for development and demonstration, not production identity or multi-role authorisation. Filtered export, assignments, configurable sorting and document upload remain hidden.
- **Performance:** List responses are paginated to 20 records and row-level evidence is fetched only on the detail route. No production SLA is claimed.
- **Maintainability:** Status transitions are centralised and tested. Synthetic browser fixtures exercise the frontend without writing test actions into official review history.
- **Security:** API and session secrets remain server-side environment variables. The application role can select and insert review events but cannot update review events or detector results.
- **Affected files:** `.env.example`, backend investigation/API/tests, frontend authentication/queue/E2E/package files, command-centre wording and project documentation.

## 2026-09-07: Export duplicate candidates as a protected human-review CSV

- **Status:** Implemented and verified.
- **Decision:** Export one row per candidate group from the latest reviewable detector run, ordered by group size and candidate ID. Include sanctioned and recommended source-record evidence, fixed decision and reason-code guidance, and blank human-review fields. Write UTF-8 with a byte-order mark, neutralise spreadsheet formula prefixes and refuse to overwrite a changed file.
- **Problem:** The 174 potential-duplicate groups require structured human verification before any conclusion. Detector JSON in PostgreSQL is complete but is not a practical review surface, and no authenticated case workflow exists yet.
- **Alternatives:** Build the investigation UI now, create an XLSX workbook, or export one row per source record. The UI would exceed the requested scope and lacks authentication and case persistence. XLSX was not requested and the spreadsheet artefact runtime was unavailable. Record-level rows would separate evidence that must be reviewed as a group.
- **Selected approach and libraries:** Add a narrow Python standard-library CSV command that reads the existing immutable detector and staging tables through Psycopg. No dependency was added. Ponytail favoured a reproducible export over a premature workflow application.
- **Trade-offs:** CSV cannot provide dropdown controls, cell protection or embedded documents. Review options are therefore supplied as text guidance columns. The generated baseline is Git-ignored and should be retained while reviewers save completed work under a separate name.
- **Performance:** The command reads 174 detector results and the associated staged sanctioned and recommended records. No production throughput claim is made.
- **Maintainability:** The column contract and allowed review values are centralised and directly tested. Content-stable reruns are allowed, while differing content at the same path is refused to protect human edits.
- **Security:** No database writes occur. Credentials remain environment-only. Formula-like source values are prefixed safely for spreadsheet programs. Raw and review data remain outside Git.
- **Affected files:** `.gitignore`, `backend/src/backend/review_export.py`, `backend/tests/test_review_export.py`, `docs/detection-rules.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`, and the ignored review CSV under `data/review/`.

## 2026-09-07: Add the official All India Lok Sabha recommended-work snapshot

- **Status:** Implemented and verified.
- **Decision:** Treat the supplied `Works Recommended.csv` as a separate official-portal snapshot with recorded All India, Lok Sabha scope. Add its exact schema to parser version 2, preserve `NA` sanction dates and unsanctioned WORK values without fabricated identifiers, and stage it as a sixth source batch.
- **Problem:** Recommended works were the missing official report needed to understand recommendation-to-sanction coverage. Its schema uses uppercase WORK, a differently labelled amount field, literal `NA` and a footer total in the final column.
- **Alternatives:** Rename source fields into the sanctioned schema, treat `NA` as an invalid date, infer Work IDs, or combine rows with sanctioned works. Each would discard source meaning or create false linkage.
- **Selected approach and libraries:** Extend the existing standard-library parser and generated dictionary. Reuse source hash/version/row provenance and Psycopg staging. No dependency was added. Ponytail favoured a narrow schema addition over a new importer.
- **Trade-offs:** Parser version 2 is required. The CSV contains no extraction timestamp, and the supplied screenshot shows slightly earlier totals. Missing sanction dates remain unknown status, not delay findings.
- **Performance:** Adds 107,157 retained records. The current in-memory inspection remains acceptable on this workstation but now has a higher measured memory ceiling; no production SLA is claimed.
- **Maintainability:** A synthetic test covers both `NA-<work type>` and linked Work IDs. Cross-report linkage is regenerated from exact normalised Work IDs.
- **Security:** Raw and processed files remain Git-ignored. No source value is overwritten and no credential is recorded. The detector rerun created a new immutable run identity rather than modifying the earlier run.
- **Affected files:** `backend/src/backend/ingest.py`, `backend/src/backend/inspect_exports.py`, `backend/tests/test_ingest.py`, generated `docs/data-dictionary.md`, `docs/source-register.md`, `docs/ingestion.md`, `docs/detection-rules.md`, `docs/PRD.md`, `docs/architecture.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`, ignored `data/` outputs and PostgreSQL staging/detector rows.

## 2026-09-07: Activate only exact duplicate-work candidate screening

- **Status:** Implemented and verified.
- **Decision:** Run one deterministic review rule over sanctioned works. Require different Work IDs and complete exact normalised matches across description, work type, State, constituency, IDA, sanction date and amount. Persist immutable run/result evidence. Keep data-quality findings separate and disable peer-cost screening after calibration.
- **Problem:** Phase 3 needs a useful, explainable shortlist without fabricating missing fields or converting broad statistical variation into accusations. Initial peer-cost calibration returned 3,016 candidates, which is unsuitable for triage given missing engineering scope.
- **Alternatives:** Activate the broad peer-cost rule, use fuzzy description similarity, assign composite risk scores, or wait for all missing fields. The first three would introduce unjustified thresholds or false precision; waiting would discard a conservative rule supported by current fields.
- **Selected approach and libraries:** Reuse Psycopg and Python standard-library `Decimal`, `statistics`, regular expressions, grouping, JSON and SHA-256. No dependency was added. Ponytail favoured one exact rule and two small immutable tables over a detector framework or ORM model layer.
- **Trade-offs:** Exact matching misses near-duplicates and can still group legitimate template-based works. The 174 groups, including groups as large as 86 records, require administrative verification. Confidence records predicate certainty only, not probability of misuse.
- **Performance:** The command reads 16,000 sanctioned detail records once and groups them in memory. The verified workstation run completed in under two seconds. No production performance SLA is claimed.
- **Maintainability:** Configuration, rule version, unavailable-detector reasons, deterministic identities and evidence contracts are centralised in `backend.detectors`. A disabled peer-cost function remains tested so recalibration is explicit.
- **Security:** Detection is a backend CLI with no public endpoint. The application role can select/insert but cannot update/delete detector tables. Credentials remain environment-only. No raw source or existing detector run was modified or deleted.
- **Affected files:** `backend/src/backend/detectors.py`, `backend/tests/test_detectors.py`, `docs/PRD.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/detection-rules.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md` and the local PostgreSQL detector tables.

## 2026-09-07: Admit the supplied allocation and calamity CSVs through the existing contract

- **Status:** Implemented and verified.
- **Decision:** Copy the two supplied CSVs unchanged into `data/raw`, verify their hashes, process them with the existing exact report contracts and stage them as separate PostgreSQL batches. Do not infer joins or activate detectors from MP names, calamity names or reconciled totals.
- **Problem:** These two report contracts existed, but the source files were previously unavailable. Their arrival changes the measured inventory, database aggregates and detector evidence.
- **Alternatives:** Rebuild the parser, combine the reports with work-level tables, or wait for XLSX/PDF counterparts. The current parser already covers the exact schemas; combining unrelated grains would create false joins; CSV inspection can proceed while missing counterparts remain explicit.
- **Selected approach and libraries:** Reuse the standard-library CSV/Decimal/hash pipeline and existing Psycopg staging path. No dependency or application code was added. Ponytail favoured the already-tested contract.
- **Trade-offs:** Allocation has no declared period or stable MP identifier, and calamity consent has no stable event/work identifier. Reconciled totals establish internal arithmetic only, not completeness or disbursal.
- **Performance:** Adds 557 retained rows across two batches. The aggregate API remains one grouped query and returns five source summaries.
- **Maintainability:** Existing versioned output and database identities remain unchanged. Missing XLSX/PDF comparisons are visible in the inspection report.
- **Security:** Raw and processed records remain Git-ignored. No credentials, destructive SQL or external repository actions were used.
- **Affected files:** `data/raw/` and `data/processed/` ignored outputs, `backend/tests/test_ingest.py`, `docs/data-dictionary.md`, `docs/detection-rules.md`, `docs/source-register.md`, `docs/ingestion.md`, `docs/PRD.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.

## 2026-09-07: Build a live data-readiness command centre before risk UI

- **Status:** Implemented and verified.
- **Decision:** Replace the Next.js starter with one server-rendered `/command-centre` route backed by a read-only aggregate FastAPI endpoint. Display only measured ingestion and data-quality information. Defer risk queues, profiles, filters, authentication and case actions until their backend logic and persistence exist.
- **Problem:** The supplied UI specification contains illustrative scores, officers, coordinates, physical progress, alerts and actions that are absent from the inspected data and application. Rendering them would fabricate government data or create dead functionality.
- **Alternatives:** Build the full visual specification with mock records, query PostgreSQL directly from Next.js, or wait for all detector phases. Mock records violate project rules; direct database access duplicates backend ownership and credentials; waiting would withhold a useful working frontend slice.
- **Selected approach and libraries:** Use installed Next.js 16.3.4 Server Components and native `fetch` to call FastAPI. Use existing FastAPI, Pydantic and Psycopg for one aggregate endpoint. Use semantic HTML and CSS for responsive presentation. The supplied reference image informs the compact light sidebar, utility header, five-metric ribbon, dense table and right analysis rail, while all illustrative content is excluded. No frontend dependency was added. Ponytail favoured native features over table, icon, state and dialog libraries for three non-interactive source summaries.
- **Trade-offs:** The page is a data-readiness command centre, not yet a risk investigation product. It has no row-level browsing or user actions. Runtime availability depends on Next.js, FastAPI and PostgreSQL processes.
- **Performance:** The browser receives three aggregate source rows rather than 34,003 records. The API performs one grouped query. No caching or performance SLA is introduced before measurement.
- **Maintainability:** Runtime response validation protects the frontend boundary. Loading, empty and error presentations are local to the route. The feature connection table records every visible flow and missing dependency.
- **Security:** Database credentials remain only in FastAPI's environment. The endpoint is read-only and returns aggregate metadata, not raw records. No fabricated authentication or officer identity appears.
- **Affected files:** `.env.example`, `backend/src/backend/main.py`, `backend/tests/test_main.py`, `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/globals.css`, `frontend/app/command-centre/page.tsx`, `frontend/app/command-centre/loading.tsx`, `frontend/next.config.ts`, `docs/feature-connections.md`, `docs/PRD.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/source-register.md`, `docs/flow.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.

## 2026-09-07: Use a project-local PostgreSQL 17 development service

- **Status:** Implemented and verified.
- **Decision:** Run the official PostgreSQL 17.11 Windows binaries from ignored project-local storage on `127.0.0.1:55432`. Use separate development and test databases, SCRAM authentication and least-privilege application roles.
- **Problem:** The staging implementation required live verification, but this workstation had no PostgreSQL service, Docker runtime or usable WSL distribution.
- **Alternatives:** Install a system-wide Windows service, enable WSL or Docker, use a remote managed database, or keep database tests mocked. System-wide installation needs machine administration, WSL was unavailable, a remote database adds credentials and network dependency, and mocks cannot verify PostgreSQL behaviour.
- **Selected approach and libraries:** Use PostgreSQL's official Windows binary distribution and the existing Psycopg binary dependency. `scripts/postgres.ps1` provides only start, stop and status operations. Ponytail favoured this small local setup over adding container or orchestration dependencies. Current PostgreSQL and Psycopg documentation was checked through Context7.
- **Trade-offs:** The 17.11 runtime and cluster consume local disk, are not committed and do not auto-start. Each team member must perform one-time local installation and role creation. Port 55432 avoids assuming the default port is free.
- **Performance:** Loopback access avoids network latency. No database throughput benchmark or production sizing claim has been made.
- **Maintainability:** The application schema remains two lossless staging tables. The script fixes the expected local path and port, making routine operation reproducible without managing a Windows service.
- **Security:** The server listens only on loopback. Host and local authentication use SCRAM. Public CONNECT is revoked. The owner role cannot log in; the application role cannot create, update or delete; tests use a separate database. Random credentials are stored only in Windows user environment variables. Local binaries, cluster files and secrets are not tracked.
- **Affected files:** `.gitignore`, `.env.example`, `scripts/postgres.ps1`, `docs/ingestion.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/PRD.md`, `docs/source-register.md`, `docs/flow.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.

## 2026-09-06: Remove mandatory acceptance quizzes

- **Status:** Accepted.
- **Decision:** Remove the rule requiring a user quiz after major coding sessions. Testing, documentation, human review and evidence-based completion checks remain mandatory.
- **Problem:** The quiz gate interrupted the development workflow without adding a technical verification result.
- **Alternatives:** Keep the mandatory quiz, or make it optional. The user explicitly requested removal.
- **Selected approach and libraries:** Delete the policy and its documentation references. No library is applicable.
- **Trade-offs:** The project loses a forced knowledge-transfer checkpoint. Reviewers can still request explanations when useful.
- **Performance:** No runtime effect.
- **Maintainability:** Fewer process-only blockers; technical acceptance remains tied to tests and documented verification.
- **Security:** No effect.
- **Affected files:** `AGENTS.md`, `docs/PRD.md`, `docs/ingestion.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.

## 2026-09-06: Preserve report snapshots and stage records without risk inference

- **Status:** Implemented and live PostgreSQL verification complete; human/source-coverage review remains.
- **Decision:** CSV is the lossless staging source. Independently inspect XLSX and retain PDF reference files. Preserve originals, footers and questionable rows; store cleaned/derived values separately with file hashes and row/line provenance.
- **Problem:** Formats contain different counts, identifiers contain whitespace, payment rows repeat Work IDs and the sanctioned footer puts money under Work Status. Earlier absent-data status is superseded by measured inspection of three report sets; allocation/calamity originals are currently missing.
- **Alternatives:** Concatenate formats, infer full project cost from payments, deduplicate on Work ID, fabricate absent fields, or build a generic spreadsheet framework. These would lose evidence or exceed the inspected contract.
- **Selected approach and libraries:** Standard-library CSV/Decimal/hash/JSON and bounded read-only XLSX XML inspection. Enable the existing Psycopg dependency's binary extra after the observed Windows libpq import failure. Context7 supplied current transaction, Jsonb and installation documentation. No ML framework, authoring library or service added. Ponytail favoured these existing/standard-library capabilities without dropping validation or tests.
- **Trade-offs:** CSV is not assumed complete. JSONB staging is not a typed analytics model. The workbook reader deliberately rejects unsupported structures. Processing is in memory for current exports. Missing inputs cannot be rerun from chat evidence.
- **Performance:** Linear report passes and set-based overlap, no pairwise similarity. Memory scales with input; no performance SLA claimed.
- **Maintainability:** Versioned parser and source-hash outputs, generated measured dictionary, refusal to overwrite inconsistent outputs and automated boundary tests. New contracts need explicit review.
- **Security:** Raw/processed records ignored in Git; no push. Environment-only credentials, parameterised SQL, explicit table creation and whole-batch transactions. No destructive SQL or file actions. Attached-document instructions are not executed.
- **Affected files:** `.gitignore`, `.env.example`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/src/backend/ingest.py`, `backend/src/backend/inspect_exports.py`, `backend/src/backend/staging.py`, `backend/tests/`, and the data/ingestion/source/flow/decision/log documents.

## 2026-09-06: Adopt the expanded brief without bypassing the dataset gate

- **Status:** Requirements baseline recorded; implementation blocked pending source data and official statement verification.
- **Decision:** Follow the latest brief's Phase 0 research, Phase 1 dataset analysis and Phase 2 ingestion numbering. Preserve earlier session labels as history. Create requested documentation now, explicitly distinguishing requirements from implementation and missing evidence from measured findings.
- **Alternatives considered:** Build a guessed schema and synthetic demo; treat public dashboard labels as source columns; defer all documentation until data arrives.
- **Reason:** The new brief authorises a fuller product but explicitly requires actual field inspection first. Requirements and source research can proceed without inventing government observations.
- **Library selection:** None added. Reuse existing stack when implementation becomes possible. Ponytail is already installed as a development plugin/skill and is not an MCP or runtime dependency.
- **Trade-offs:** Real ingestion and detectors remain blocked; the documents make the missing inputs and acceptance gates reproducible rather than masking them with a scaffold.
- **Maintainability impact:** One linked requirements baseline and explicit current-state documents reduce accidental implementation against unsupported assumptions. Detector classifications must be reassessed after each dataset revision.
- **Performance impact:** No runtime change; no benchmarks or optimisation claims.
- **Security impact:** No credentials, raw government records, external writes or repository actions introduced. No additional MCP installed.
- **Affected files:** `docs/PRD.md`, `docs/techstack.md`, `docs/architecture.md`, `docs/data-dictionary.md`, `docs/detection-rules.md`, `docs/source-register.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.

## 2026-09-06: Keep MCP configuration project-scoped and minimal

- **Status:** Accepted
- **Decision:** Enable project-scoped Context7 and Playwright MCPs, configure Google Stitch as disabled until credentials are supplied, and defer GitHub MCP until a repository exists.
- **Problem being solved:** The project needs current technical documentation and browser QA without adding broad, speculative or destructive tool access.
- **Alternatives considered:** User-level-only MCP configuration; adding filesystem, database and deployment MCPs; enabling GitHub before a remote exists; enabling Stitch by default.
- **Selected approach and reason:** Project-scoped configuration is reproducible for the team and limits the project to tools with an immediate purpose. Context7 uses its maintained remote endpoint. Playwright is pinned and isolated. Stitch is credential-gated. GitHub is deferred.
- **Library selection:** `@playwright/mcp` was selected because it is the official Playwright MCP implementation. No local Context7 library is required because the maintained remote endpoint is used.
- **Trade-offs:** Team members must trust the project and restart Codex. Stitch requires a manual enablement step. The single default browser configuration does not replace cross-browser test runs.
- **Performance impact:** Optional MCP startup adds small local or network latency. Servers are not required, so an unavailable optional server does not block Codex startup.
- **Maintainability impact:** One tracked TOML file and pinned Playwright version make the setup reproducible but require deliberate version review.
- **Security impact:** Playwright is origin-limited and isolated, its arbitrary-code tool is disabled, Stitch deletion is disabled, credentials remain in environment variables, and GitHub will begin read-only.
- **Affected files:** `.codex/config.toml`, `.env.example`, `.gitignore`, `AGENTS.md`, `docs/mcp-setup.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.

## 2026-09-06: Establish permanent product and engineering guardrails

- **Status:** Accepted
- **Decision:** Make root `AGENTS.md` the mandatory repository-wide development policy and require factual decision, flow and session records.
- **Problem being solved:** Risk-intelligence software using government data needs durable controls for claims, provenance, explainability, generated content, accessibility, security and feature completeness.
- **Alternatives considered:** Keep rules only in chat prompts; scatter rules across tool-specific files; document only technical conventions; postpone governance until feature development.
- **Selected approach and reason:** A root policy applies to the whole repository and is visible before work begins. Focused documents retain decision history, actual execution flow and session evidence.
- **Library selection:** Not applicable. This is a repository governance and documentation decision.
- **Trade-offs:** Documentation adds session overhead. The benefit is an auditable record and fewer silent safety or architecture regressions.
- **Performance impact:** No runtime impact. Development sessions include small documentation and verification costs.
- **Maintainability impact:** Central rules reduce duplication, while named documentation files create clear ownership. The files must be updated whenever implementation changes.
- **Security impact:** The policy prohibits committed credentials, requires input validation and explicit approval for destructive operations, and keeps generative AI outside risk-flag decisions.
- **Affected files:** `AGENTS.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.
