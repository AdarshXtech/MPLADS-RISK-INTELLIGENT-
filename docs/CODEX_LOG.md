# Codex log

## 2026-09-08: Investigate frontend CI installation failure

- **Evidence:** GitHub run `34249019121` at `4e2ebf5` reports Backend success and Frontend failure in Install locked dependencies. The annotation reports exit code 1; detailed logs require authentication (HTTP 403).
- **Reproduction and change:** npm 10.9.9 locally rejected the lock with missing `@emnapi/core@1.11.3` and `@emnapi/runtime@1.11.3`. Regenerated `frontend/package-lock.json` using npm 10 without changing direct dependencies or weakening `npm ci`. Dry-run lock validation then passed with npm 10.9.9 and npm 11.6.2. Local checks use Windows and Node.js 24.13.0; hosted CI uses Linux and Node.js 22, so local success is not a hosted-run result.
- **Files:** Frontend lockfile, decisions, flow and this log. The previously tested responsiveness changes remain intact.
- **Verification:** Clean npm 10 installation, ESLint and production build passed. All 45 Playwright tests passed across Chromium, Firefox and WebKit (3.9 minutes). Prepared one local commit including the previously verified responsive work and this lock repair. A new hosted run is still needed to confirm the remote failure is resolved. No push or deployment was performed.

## 2026-09-08: Responsive layouts and scenario screenshots

- **Task:** Improve website responsiveness and provide images of the implemented screens and interaction states.
- **Created:** `frontend/e2e/responsiveness.spec.ts`, `frontend/e2e/build-gallery.mjs`, `docs/responsive-ui.md`; ignored PNGs under `output/responsiveness/`.
- **Modified:** Shared CSS; queue shell; Command Centre, queue and candidate evidence page focus targets; synthetic mock API; decisions, flow, feature connections, deployment, techstack and this log.
- **Implementation:** Wrapping phone navigation and headers, fluid laptop filters, touch-sized actions, tablet/phone metric grids, cards for narrow source columns, long-evidence wrapping and a scrollable desktop sidebar. Explicit skip-link and main-target tab indices fix WebKit keyboard entry and focus transfer. Existing components and platform APIs were reused without adding dependencies.
- **Scenario coverage:** Eight viewport sizes from 320 to 1920 pixels in Chromium, Firefox and WebKit. Normal routes, sign-in failure, empty/filtered/paginated queues, export pending/error/success, candidate missing/service error, review failure and status transitions, Command Centre empty/error, both route-loading states, recovery links, reduced motion, long values and a 640-pixel reflow/keyboard case. Optional screenshots have a visible synthetic-data label and never modify official review history.
- **Verification:** ESLint and the production build passed. All 45 Playwright tests passed across Chromium, Firefox and WebKit in the final run (4.5 minutes). Generated 297 scenario PNGs, 99 per browser. Gallery checks passed for browser/size filtering, opening full-resolution PNGs and 320-pixel layout. Representative phone, tablet, laptop, error, loading and long-evidence images were visually inspected. Initial checks exposed Next.js's separate route-announcement alert, so error assertions were scoped to main content. A minimal WebKit page reproduced skipped implicit link focus; explicit tabindex fixed the cause. Removed an unreliable local-file download link in favour of opening the full image. The gallery and images are packaged in `output/mplads-responsive-ui.zip`.
- **Limitations:** Screenshots use the isolated synthetic API. Responsive viewport emulation and reflow checks do not certify physical devices, native 200% browser zoom or all WCAG criteria. Backend behaviour and data are unchanged; PostgreSQL tests are not rerun for these presentation/test changes. No commit, push or deployment is performed for this task.

## 2026-09-08: Add GitHub Actions CI

- **Task:** Take the next deployment-preparation step after synchronising the repository.
- **Created:** `.github/workflows/ci.yml`.
- **Modified:** `frontend/package-lock.json`, `docs/deployment.md`, `docs/decisions.md`, `docs/flow.md`, `docs/techstack.md` and this log.
- **Implementation:** Added two read-only jobs for pushes and pull requests to `master`, plus manual dispatch. Backend CI uses pinned uv 0.12.10, Python 3.12 and an ephemeral PostgreSQL 17 service for Ruff and all Pytest checks. Frontend CI uses Node.js 22 for ESLint and the existing Playwright-managed production build and nine Chromium, Firefox and WebKit tests. Action dependencies are pinned to current commit hashes. Reconciled npm's optional WASI package metadata after a clean npm 11 install found the committed lock internally inconsistent. No deployment provider, application dependency, GitHub secret or official dataset was added.
- **Guidance checked:** Current official GitHub service-container and minimum-token-permission documentation, Astral uv GitHub Actions guidance and Playwright CI guidance. Context7 confirmed the current three-browser Playwright installation and execution pattern. Ponytail kept provider-specific deployment and extra CI machinery out of scope.
- **Verification:** `uv sync --frozen`, Ruff formatting, Ruff lint and all 50 PostgreSQL-backed Pytest tests passed. A clean `npm ci` reported zero vulnerabilities, ESLint passed, the production build succeeded and all nine Playwright tests passed across Chromium, Firefox and WebKit. The hosted GitHub Actions result remains pending until the workflow is pushed.
- **Known limitations:** Browser tests use the existing synthetic mock API, not a staging URL. Branch protection and hosting remain manual decisions. The workflow validates changes but does not deploy them.

## 2026-09-08: Verify GitHub synchronisation

- **Result:** The user completed the pending normal push to `origin/master`. A read-only remote check confirmed local and remote commit `0a02d29bfe0c329226a47d9f39e948b23d6f3689` match exactly, with no ahead/behind difference and a clean working tree.
- **Safety:** No force-push, branch deletion, merge or repository-setting change occurred. Application tests were not rerun because this verification changed documentation only.
- **Next deployment gate:** Select the private staging host, region, managed PostgreSQL service and secret store before provider-specific deployment configuration is added.

## 2026-09-08: Push the initial GitHub baseline

- **Task:** Continue the approved deployment preparation by publishing the reviewed local baseline to the configured GitHub remote.
- **Action:** Pushed local commit `55db3c3d85b69c2bc06d1f0da1cc4fa93a4c66f9` to the new `origin/master` branch and configured local `master` to track it. The local and remote hashes matched after the push.
- **Safety:** Used a normal push. No force-push, branch rename/deletion, merge, issue, pull request, repository setting, secret or deployment resource was changed.
- **Documentation:** Updated deployment readiness and the existing baseline decision to record the completed baseline push. The documentation follow-up remains local because reusable GitHub authentication was unavailable.
- **Push issue:** The first follow-up attempt stalled without output and was stopped after remote verification showed no partial update. A non-interactive retry failed explicitly because Git Credential Manager could not provide a GitHub username. GitHub CLI is not installed. Local `master` is ahead of `origin/master`; no credential was exposed or persisted.
- **Remaining manual decisions:** Confirm whether `master` remains the default branch or should later be renamed to `main`; configure branch protection and collaborator permissions in GitHub; select the private staging host, region, managed PostgreSQL and secret store.

## 2026-09-08: Prepare the local initial commit for private staging

- **Task:** Start the first deployment action by reviewing and committing the project locally, without pushing or publishing externally.
- **Repository audit:** The configured GitHub remote responded successfully and contained no branch. Seventy-six initial candidates were inspected; generated `output/` was then excluded, leaving the project source set plus a new root README. `data/raw`, `data/processed`, `data/review`, `.local`, environment files, browser results, dependencies and Next.js build output are ignored.
- **Secret check:** No private-key block, GitHub token, OpenAI-style key, AWS access key or credential-bearing PostgreSQL URL pattern was found. The only broad credential-word match was the Playwright configuration, which generates test-only values at runtime.
- **PDF check:** The nine-page explanatory PDF was rendered and visually inspected. It is readable and contains no detected secret pattern, but it documents the older CSV-only review stage. It remains safely on disk under ignored `output/` and is not included in the deployment baseline.
- **Documentation:** Added project-specific root/backend/frontend READMEs. Updated deployment readiness and the technical decision record. No application behaviour, detector, database schema or official data changed.
- **Verification inherited immediately before staging:** 50 Pytest tests, ESLint, the Next.js production build and 9 Playwright tests across Chromium, Firefox and WebKit passed on the current application code. Staging checks include `git diff --cached --check` and exact file review.
- **External actions:** A local initial commit is created after the final staged review. No push, branch protection, CI, hosting resource or deployment is performed. Manual next step is to confirm the GitHub destination/branch policy and select the private staging host, region and managed PostgreSQL service.

## 2026-09-07: Add real queue workload to the protected Command Centre and assess deployment

- **Task:** Start the next product step by connecting current investigation workload to the Command Centre, then define an honest deployment path.
- **Created:** `docs/deployment.md`.
- **Modified:** `backend/src/backend/investigations.py`, `backend/src/backend/main.py`, `backend/tests/test_investigations.py`, `frontend/app/command-centre/page.tsx`, `frontend/app/investigation-queue/shell.tsx`, `frontend/lib/investigations.ts`, `frontend/app/globals.css`, E2E mock/tests, PRD, architecture, techstack, feature connections, investigation-queue guide, decisions, flow and this log.
- **Implementation:** Added protected `GET /investigation-summary` and one aggregate query over the latest reviewable run/latest append-only event. The authenticated Command Centre now shows total candidate groups, New, Under review, Verification requested and Closed counts, and links to the queue. Command Centre access now requires the signed reviewer session. Reused the existing shell and added no dependency or chart. Detection results remain immutable.
- **Verification:** Ruff and Ruff format checks passed. Pytest passed 50 tests with no skips against the dedicated PostgreSQL test database. ESLint and the Next.js 16.3.4 production build passed. Playwright passed 9 tests across Chromium, Firefox and WebKit, covering protected Command Centre access, live-style workload rendering, the queue link and existing controls/responsive flows.
- **Live read-only result:** 174 total candidates, 174 New, and zero Under review, Verification requested, Resolved and Dismissed. No official review event, source row or detector result was written.
- **Deployment decision:** Documented a first private staging shape with HTTPS ingress, one Next.js instance, private FastAPI and private TLS PostgreSQL. Context7 and installed official Next.js self-hosting guidance confirmed runtime server-only variables and reverse-proxy guidance. Ponytail prevented speculative cloud/Docker configuration before a target is selected.
- **Deployment blockers/manual work:** The Git remote exists, but the repository has no initial commit and all project files are untracked. Hosting target, region, domain, production database/backups, secure source-data transfer, secret store, monitoring and approved organisational identity are unavailable. No deployment, commit or push was performed.

## 2026-09-07: Complete Investigation Queue sorting

- **Task:** Implement the remaining configurable queue sorting capability as the next workflow step.
- **Modified:** Backend investigations/main and their tests; frontend investigation queue page, investigations types, export route, global CSS, E2E mock/tests; PRD, architecture, techstack, feature-connections, decisions, flow, investigation-queue guide and this log.
- **Implementation:** Added four whitelisted server-side orders with stable result-ID tie-breaking. Sorting persists through filters and pagination and controls CSV order. Unknown frontend URL values return to the safe default; FastAPI publishes a closed enum. No dependency or database schema change was introduced. Ponytail kept the design to one native select and one SQL whitelist.
- **Tests:** `uv run ruff check src tests` and Ruff format check passed. Pytest passed 49 tests with no skips against the dedicated PostgreSQL test database. `npm run lint` passed. The final production-build Playwright run passed 9 tests across Chromium, Firefox and WebKit. An earlier rerun exposed a Firefox timing race because the test navigated before sign-in completed; waiting for the queue after sign-in corrected the test, and the complete suite then passed.
- **Coverage:** Default/smallest, largest, recent-review and CSV ordering; closed API enum; State ordering surviving pagination; invalid URL fallback; responsive native select and existing keyboard workflow.
- **Data integrity:** No detector, source or review records were modified. A live read-only check found 174 candidates; smallest order began with 2-record groups, largest order with 86, 49, 42, 41 and 33 records, and State order with Andhra Pradesh. The review-event count remained zero. Sorting changes presentation only and does not change flags, severity or confidence.
- **Limitations/manual review:** The current dataset does not justify amount ordering across potentially ambiguous units. There is no user-configurable arbitrary field or direction and no new index at the current 174-group scale. Production identity remains unresolved.

## 2026-09-07: Filtered queue CSV and evidence visibility

- **Task:** Continue the queue with authenticated all-matching-results CSV export without changing detection.
- **Created:** `frontend/app/investigation-queue/export/route.ts`, `frontend/app/investigation-queue/export-button.tsx`, `docs/investigation-queue.md`.
- **Modified:** Backend investigations, main, review_export and investigation tests; frontend queue page, investigations client, global CSS, E2E mock API/tests; PRD, architecture, techstack, feature-connections, decisions, flow and this log.
- **Implementation:** Shared literal-search/state/status filters; all-pages export with a 10,000-group refusal limit; provenance, rule version and latest review details; formula-safe UTF-8 CSV; pending/success/error feedback. Fixed source cards hidden on desktop by a later CSS rule. Ponytail guided reuse without new dependencies.
- **Tests:** Ruff and ESLint passed. Pytest: 47 passed, no skips, using the dedicated PostgreSQL test database. Playwright production build and 9 tests passed across Chromium, Firefox and WebKit.
- **Coverage:** Existing authentication, filters, pagination, review/evidence and phone/tablet keyboard checks; new unauthenticated download refusal, all-pages CSV, filtering, empty CSV, failure feedback/retry availability, formula neutralisation, provenance/latest-event retention and limit refusal. Corrected an initial test assumption: literal underscores can match JSON evidence field names.
- **Live read-only check:** 174 exported candidates, 1,281 source references, detector version 1, 489,951 bytes. Official review-event count remained zero. No source, detector or review rows changed. Browser write tests use synthetic fixtures only.
- **Limitations/manual steps:** Browser tests use a synthetic API; live MCP browser QA was not repeated this session. No full accessibility audit, production identity, configurable sorting, full-history CSV, re-import or deployment. Existing run-selection order is unchanged. Configure reviewer credentials and handle downloaded evidence securely as explained in the queue guide. Automatic restart after token replenishment is unavailable.

## 2026-09-07: Start the authenticated Investigation Queue

- **Task:** Build the first complete Investigation Queue slice over the 174 real potential-duplicate candidate groups, without adding a decorative dashboard or unsupported detectors.
- **Files created:** `backend/src/backend/investigations.py`, `backend/tests/test_investigations.py`, `frontend/lib/auth.ts`, `frontend/lib/investigations.ts`, login and Investigation Queue routes, synthetic Playwright fixture/API, Playwright configuration and E2E tests.
- **Files modified:** `.env.example`, `backend/src/backend/main.py`, command-centre wording/navigation, frontend CSS/package files, and the PRD, architecture, detector, feature-connection, decision, flow and session-log documents.
- **Implementation:** Added protected list/detail/event FastAPI endpoints, server-side search, State/status filtering, 20-row pagination, source provenance, limitations and verification guidance. Added single-account local sign-in with an eight-hour HMAC-signed HTTP-only cookie and a server-only API key. Added append-only review events with explicit status transitions, mandatory final decisions and mandatory dismissal reasons. Reviewer actions cannot change detector results.
- **Database:** Created `mplads_review_event` in the local development database. `mplads_app` has SELECT/INSERT and no UPDATE on that table, and still has no UPDATE on detector results. Live application-role verification returned 174 candidates, 20 records on page one and 17 State values. No official candidate received a test review action.
- **Verification:** Ruff passed. Pytest passed 44 tests with live PostgreSQL integration. ESLint and the Next.js 16.3.4 production build passed. Local Playwright passed six E2E tests across Chromium, Firefox and WebKit, covering invalid/valid login, authentication redirect, search, filters, pagination, evidence detail, review controls, saved audit history, navigation, keyboard focus, phone/tablet layouts, overflow checks and sign-out. HTTP checks confirmed protected API requests return 401 without the key and 200 with the server key.
- **MCP verification:** Temporary ports 3010 and 8010 were outside the configured allowed origins and correctly returned `net::ERR_BLOCKED_BY_CLIENT`. Retesting at the permitted `http://localhost:3000` origin passed live checks for authentication, the 174-candidate total, pagination, combined search/State/status filters, real evidence and provenance, unsaved form interaction, visible keyboard focus, phone/tablet overflow, navigation and sign-out. The only console error was a blocked Kaspersky-injected script; application requests returned 200. The save action was intentionally not submitted against official review history; its browser behaviour passed against the synthetic local E2E service.
- **Known limitations:** Local authentication supports one reviewer and is not production identity. Configurable sorting, filtered export, assignment, document upload, composite scoring and project dossiers remain unimplemented and are not displayed. Set `MPLADS_SECURE_COOKIES=false` only when testing production-mode Next.js over local HTTP.
- **Manual setup:** Configure `MPLADS_REVIEW_USERNAME`, `MPLADS_REVIEW_PASSWORD`, `MPLADS_SESSION_SECRET` and `MPLADS_REVIEW_API_KEY` outside Git. Other databases require an administrator to create the review table and grant the same least privileges.

## 2026-09-07: Create and expand the simple project explainer PDF

- **Task:** Create a plain-language PDF explaining what the MPLADS Risk Intelligence and Early Warning System is, how the current implementation works and how the complete Smart Automation workflow will work.
- **File created:** `output/pdf/mplads-risk-intelligence-explained.pdf`.
- **Content:** Nine A4 pages covering what the product is, the supplied official datasets, current implementation, end-to-end working flow, code ownership by file, real function-call chains, PostgreSQL tables, the 174 duplicate-candidate groups, the planned future workflow, AI boundaries, safeguards and the recommended next step.
- **Implementation:** Generated with ReportLab in an isolated `uv` environment and assembled with pypdf. No application dependency or runtime code changed. The language avoids unsupported findings and clearly states that candidate groups are not confirmed duplicates.
- **Verification:** Rendered all nine pages to fresh PNG files using Poppler and visually inspected every page. Headers, tables, code-flow boxes, diagrams, spacing, page numbers and footers are readable with no clipping or overlap. Pypdf confirmed nine pages, the required product, working-flow and code sections, page labels 1 through 9 and no em dash or non-breaking hyphen characters. Final size is 24,850 bytes and SHA-256 is `b1f2b5ccca565d7ed2d7348e17765eaa0407d30b80d451289c389f82353a3576`.
- **Known limitation:** The PDF explains the verified project state as of 7 September 2026. It is not an official MoSPI publication and must be updated when detectors, data coverage or the review workflow change.

## 2026-09-07: Create the duplicate-candidate human-review CSV

- **Task:** Start structured human review of the 174 potential-duplicate groups produced by the active deterministic detector.
- **Files created:** `backend/src/backend/review_export.py`, `backend/tests/test_review_export.py`, and the Git-ignored `data/review/duplicate-candidate-review-1f30a547592b-final.csv`.
- **Files modified:** `.gitignore`, `docs/detection-rules.md`, `docs/decisions.md`, `docs/flow.md` and `docs/CODEX_LOG.md`.
- **Implementation:** Added a read-only export command that selects the latest reviewable run, creates one row per group, preserves sanctioned source-record provenance and enriches exact Work IDs with recommended-work references, dates and amounts. The 30-column contract includes match basis, verification guidance, limitations, fixed decision/reason options and eight blank human-review fields. Groups are sorted smallest first. UTF-8 byte-order-mark output supports Excel, formula-like values are neutralised and changed content cannot overwrite an existing review file.
- **Data result:** The final CSV contains 174 unique candidate groups, all with sanctioned and recommended source references. Group sizes range from 2 to 86, including 60 two-record groups. All human-review fields are blank. File size is 609,164 bytes and SHA-256 is `bdcc0c8f68d3d8d9fccde1ac10a9387e3bd006ef22a433ceb2b1671a7f14f317`.
- **Verification:** Direct CSV parsing confirmed 174 rows, 30 headers, 174 unique candidate IDs, no missing sanctioned evidence, no populated human-review fields, no direct formula-risk prefixes and a valid UTF-8 byte-order mark. `uv run --frozen pytest -q` passed all 39 tests against the local PostgreSQL test database in 2.23 seconds. Ruff formatting and repository-wide checks passed.
- **Known limitations:** The spreadsheet artefact runtime was unavailable in this session, so workbook authoring and rendered visual inspection could not be used. The requested plain CSV was created with the existing standard-library path and verified structurally. CSV cannot provide dropdowns, protected cells or embedded source documents. The export is a review aid, not a duplicate determination or proof of misuse.
- **Manual review:** Open the final CSV in Excel, examine the supplied source evidence and official supporting records, complete the blank review columns, and save the reviewed copy under a new filename. Use `INSUFFICIENT_EVIDENCE` where records cannot establish whether works are separate or duplicated.

## 2026-09-07: Add official All India Lok Sabha recommended works

- **Task:** Inspect and ingest the supplied official-portal `Works Recommended.csv`, with user-confirmed All India and Lok Sabha scope.
- **Files added locally:** One unchanged Git-ignored raw copy and its parser-version-2 processed output. Downloads/raw SHA-256 is `f9ceb495b8a211da2bdac423c19d1690aa2a2e5845062f7adc71232f4dc204b4` on both copies.
- **Files modified:** `backend/src/backend/ingest.py`, `backend/src/backend/inspect_exports.py`, `backend/tests/test_ingest.py`, generated `docs/data-dictionary.md` and `data/processed/inspection.json`, plus `docs/source-register.md`, `docs/ingestion.md`, `docs/detection-rules.md`, `docs/PRD.md`, `docs/architecture.md`, `docs/decisions.md`, `docs/flow.md` and `docs/CODEX_LOG.md`.
- **Implementation:** Added the exact eleven-column schema. Parser version 2 treats literal `NA` in Sanction Date as missing and derives work type, but no Work ID, from `NA-<work type>`. Existing Work IDs keep whitespace-only derived normalisation. Original cells remain unchanged.
- **Data result:** 107,156 detail rows and one summary row; INR 57,398,544,852.41 listed sum exactly reconciles with the footer. There are 78,919 distinct Work IDs, 28,237 missing sanction dates, two missing descriptions, 1,689 exact repeated details ignoring serial and no repeated derived Work IDs. PostgreSQL now contains six batches and 141,717 retained records; 32,839 records contain validation issues.
- **Linkage:** Recommended works share 15,963 IDs with sanctioned, 8,166 with expenditure and 6,988 with completed reports. Coverage and snapshot timing remain unverified, so unmatched records are not classified as delays or omissions.
- **Detector impact:** The active rule still produces 174 potential-duplicate groups. A new immutable engine-version-2 run ties the same results to all six current source batches. Recommended data is not silently added to the rule predicate.
- **Verification:** `uv run --frozen pytest -q` passed 38 tests in 1.50 seconds with live PostgreSQL integration. Ruff formatting and checks passed. Dictionary and inspection outputs were byte-identical on rerun; final Downloads/raw hashes matched. Re-staging reported an identical batch. The live API returned six sources, 141,717 retained rows and 32,839 review rows. Frontend ESLint passed. Playwright confirmed the recommended source, Indian-formatted `1,41,717` total, six desktop rows, six mobile cards, working navigation and no horizontal overflow at 360 pixels. The only browser console error was the previously observed blocked Kaspersky-injected script; application requests succeeded.
- **Known limitations:** The portal screenshot showed 107,135 works and INR 5,735.81 crore, while this CSV has 21 more rows and INR 5,739.85 crore. Exact extraction time is unavailable. Recommended XLSX/PDF counterparts, physical locations, quantities and amendment history were not supplied.

## 2026-09-07: Phase 3 deterministic duplicate-work candidate rule

- **Task:** Start Phase 3 with explainable deterministic rules and PostgreSQL persistence, without adding a dashboard or unsupported claims.
- **Files created:** `backend/src/backend/detectors.py`, `backend/tests/test_detectors.py`.
- **Files modified:** `docs/PRD.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/detection-rules.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`. PostgreSQL gained `mplads_detector_run` and `mplads_detector_result`.
- **Implementation:** Added deterministic source/config/result identities; exact duplicate-work grouping across seven fields with different Work IDs; full source-row provenance; fields used, evidence, explanation, verification guidance, limitations, rule version, review severity and predicate confidence. Four unsupported detectors are stored with missing-input reasons. Data-quality issues remain separate.
- **Calibration:** An initial engine-version-1 peer-cost calibration produced 3,016 cost candidates plus 174 duplicate candidate groups. This was rejected as too broad because category/type groups lack quantities, dimensions, unit rates and revisions. The run is retained as `calibration` for auditability. Engine version 2 disables peer cost and is the only `reviewable` run.
- **Data result:** The reviewable run contains 174 potential-duplicate groups referencing 1,281 sanctioned source records. Group sizes range from 2 to 86, and 60 groups contain exactly two records. These are verification candidates, not findings of duplication, misuse or fraud. No score or frontend/API exposure was added.
- **Database verification:** The restricted application role reproduced the same run ID and reported no reinsertion. It has SELECT/INSERT and no UPDATE/DELETE rights on detector tables. No detector data was deleted or overwritten.
- **Tests:** `uv run --frozen pytest -q` passed 37 tests in 1.36 seconds with the live PostgreSQL integration enabled. Ruff formatting for the new files and repository-wide Ruff checks passed. Synthetic tests cover deterministic output, required fields, different Work IDs, peer threshold/minimum behaviour, peer-rule disablement, PostgreSQL persistence and idempotency. A final application-role run reproduced the same run ID and 174-result hash without reinsertion.
- **Known limitations:** The exact rule can miss near-duplicates and can group legitimate template-based records. Asset identity, coordinates, quantities and official duplicate-review policy are unavailable. Peer-cost screening remains disabled. No detector API, composite score or investigation workflow exists.
- **Manual review:** Officials must inspect the underlying recommendation, location, asset, quantity and sanction records before any conclusion. Obtain verified engineering fields before reconsidering peer cost.
- **Browser verification:** Not run because this phase changed no frontend route or API response. Existing detector results are intentionally not exposed in the product UI.

## 2026-09-07: Inspect and stage allocation and calamity CSVs

- **Task:** Include the newly supplied `Allocated Limit for Honble MPs.csv` and `Amount consented for Calamity.csv` in the existing Phase 2 inspection and ingestion flow.
- **Files added locally:** Two unchanged, Git-ignored raw copies and two versioned processed output directories. Source/raw SHA-256 hashes match for both files.
- **Files modified:** Added synthetic allocation/calamity coverage to `backend/tests/test_ingest.py`; generated `docs/data-dictionary.md` and `data/processed/inspection.json`; updated `docs/detection-rules.md`, `docs/source-register.md`, `docs/ingestion.md`, `docs/PRD.md`, `docs/decisions.md`, `docs/flow.md` and `docs/CODEX_LOG.md`. No application or dependency code changed.
- **Data result:** Allocation has 543 detail rows and one summary row; one allocation amount is blank and remains null. Calamity has 12 detail rows and one summary row with no validation issues. Both listed sums reconcile with their respective footers. PostgreSQL now contains five batches and 34,560 retained records, comprising 34,555 detail and five summary records; 3,159 records have validation issues.
- **Detector result:** Existing feasibility classifications remain unchanged. The new fields add supplementary allocation and consent context but lack allocation period, stable MP/event identifiers, work linkage and verified compliance rules. They do not make a risk detector fully supported.
- **Verification:** Exact schemas accepted. Generated dictionary and inspection outputs were byte-identical on rerun. Final Downloads/raw hashes matched. Repeat staging reported both batches identical. The PostgreSQL integration suite passed 32 tests in 1.15 seconds and Ruff passed. Frontend ESLint passed. The live API returned five sources, 34,560 retained rows and 3,159 review rows. Playwright confirmed both new sources and all aggregate counts at desktop and 360-pixel phone widths, five mobile source cards, no horizontal overflow, working navigation links and visible keyboard focus. The only browser console error was the previously observed blocked Kaspersky-injected script; application requests succeeded.
- **Known limitations:** Allocation/calamity XLSX and PDF counterparts were not supplied. Exact export filters, coverage, allocation period and calamity scope remain unverified. Consent is not treated as payment, and no name-based join or risk flag was created.

## 2026-09-07: Align command centre with supplied visual reference

- **Task:** Apply the supplied command-centre screenshot as a visual reference without copying its invented data or inactive controls.
- **Files modified:** `frontend/app/command-centre/page.tsx`, `frontend/app/globals.css`, `docs/feature-connections.md`, `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.
- **Implementation choices:** Reused the live API and existing components. Added the light administrative sidebar, compact scope strip, five-cell metric ribbon and right analysis rail. Validation bars use each source's actual issue-to-detail ratio. Pipeline statuses describe verified implementation state. No dependency or new route was added.
- **Tests:** Backend PostgreSQL suite: 30 passed in 1.88 seconds; Ruff passed. Frontend ESLint and Next.js production build passed. Playwright verified the live page at 1,536-pixel desktop and 360-pixel phone widths, mobile card substitution, no horizontal overflow, both navigation links and keyboard focus. The existing browser-injected Kaspersky script remained the only console error; application requests succeeded.
- **Limitations:** The reference's risk records, alert totals, filters, search, export, officer profile and administrative actions remain omitted because their data, APIs, authentication and persistence do not exist. Chromium was the only browser available through the configured MCP.

## 2026-09-07: Live data-readiness command centre

- **Task:** Begin frontend work using all currently available data while following the supplied UI and zero-guesswork specifications.
- **Files created:** `frontend/app/command-centre/page.tsx`, `frontend/app/command-centre/loading.tsx`, `backend/tests/test_main.py`, `docs/feature-connections.md`.
- **Files modified:** `.env.example`, `backend/src/backend/main.py`, `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/globals.css`, `frontend/next.config.ts`, `docs/PRD.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/source-register.md`, `docs/flow.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.
- **Implementation choices:** Built one complete server-rendered route instead of reproducing illustrative risk data. The root redirects to `/command-centre`; Next.js requests a new aggregate FastAPI endpoint; FastAPI reads PostgreSQL with the existing restricted application role. The browser receives source metadata and counts only. Native platform and installed framework features avoided new frontend dependencies.
- **Data shown:** Three staged reports, 34,003 retained records, 34,000 detail records and 3,158 records requiring data-quality review. The page explicitly states that validation issues are not risk flags and that risk prioritisation is unavailable.
- **Tests executed:** Backend PostgreSQL suite and Ruff; frontend ESLint and production build; direct HTTP checks for all three FastAPI routes; Playwright navigation for `/` and `/command-centre`; every product link; keyboard entry and skip link; 360-pixel phone, 768-pixel tablet and 1,536-pixel desktop layouts; reflow-equivalent viewport; service outage, retry while unavailable and retry after recovery; frontend and backend process logs; browser console and network inspection.
- **Results:** 30 backend tests passed; the final run completed in 1.43 seconds, and Ruff passed. ESLint and the Next.js 16.3.4 production build passed. Root redirected correctly, live data matched PostgreSQL, mobile source cards replaced the desktop table, no horizontal overflow was found and service recovery succeeded. The only browser console/network error was a blocked Kaspersky browser-injected script outside the application; application requests returned successfully.
- **Known limitations:** Configured Playwright MCP used Chromium only; Firefox and WebKit were not available in this MCP session. The transient loading presentation and non-empty database's empty state compiled but were not retained for a live assertion. No authentication, detector, risk score, project dossier or case action exists. These controls were intentionally omitted.
- **Manual review:** Review the information hierarchy and wording against the intended administrative workflow. Do not approve illustrative values from the supplied design specification as government data.
- **Unresolved issues:** Source coverage/filters remain unverified. Detector, risk API and authentication phases must precede investigation controls and project risk profiles.

## 2026-09-07: Local PostgreSQL setup and live integration verification

- **Task:** Set up PostgreSQL for the project and run the integration test.
- **Files created:** `scripts/postgres.ps1`; ignored local PostgreSQL 17.11 runtime and cluster state under `.local/`.
- **Files modified:** `.gitignore`, `.env.example`, `docs/ingestion.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/PRD.md`, `docs/source-register.md`, `docs/flow.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.
- **Implementation choices:** Used the official PostgreSQL 17.11 Windows x86-64 archive without adding Docker, WSL, a Windows service or a new application dependency. Bound the server to `127.0.0.1:55432`, enabled SCRAM authentication, separated development/test databases and used non-login ownership plus restricted application access. Credentials are random and stored only as Windows user environment variables. Added a minimal start/stop/status script.
- **Data result:** Staged the three available CSV reports as three batches containing 34,003 records, including three summary records and 3,158 records with validation issues. Validation issues remain evidence for review and do not create risk flags. Re-running all imports reported identical batches and inserted no duplicates.
- **Tests executed:** `uv run --frozen pytest -q` with `TEST_DATABASE_URL`; `uv run --frozen ruff check --no-cache src tests`; application-role privilege queries; incorrect-password connection; server stop/start; post-restart row counts.
- **Results:** 29 tests passed with no skip; the most recent run completed in 1.65 seconds. Ruff passed. The application role is not superuser and cannot create databases, roles or schema objects; it can SELECT/INSERT staging records but cannot UPDATE/DELETE. An incorrect password was rejected. Restart retained all three batches and 34,003 records.
- **Setup issues resolved:** No PostgreSQL, Docker or usable WSL installation existed. An initial password-prompt bootstrap was interrupted before creating a cluster. A subsequent non-interactive cluster bootstrap completed, all credentials were rotated to random values, trust authentication was replaced with SCRAM and the configuration was reloaded before verification.
- **Known limitations:** This is a workstation-local development service, not a production deployment, backup strategy or performance benchmark. Runtime files and credentials are intentionally untracked. Source completeness and the missing allocation/calamity exports still require human review. No detector or dashboard work was performed.
- **Manual action:** Open a new terminal if the user-level environment variables are not visible. Use `scripts/postgres.ps1 start` after a reboot. Other team members must install an equivalent local PostgreSQL 17 runtime and create their own credentials.

## 2026-09-06: Remove mandatory quiz rule

- **Task:** Removed the mandatory major-change acceptance quiz at the user's request.
- **Files modified:** `AGENTS.md`, `docs/PRD.md`, `docs/ingestion.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.
- **Decision:** Future work no longer requires a user quiz before acceptance. Normal testing, documentation, review and verification requirements remain unchanged.
- **Tests:** Repository-wide search confirmed no remaining project quiz or knowledge-check requirement. Documentation punctuation checks passed. No application code changed, so runtime tests were unnecessary.


## 2026-09-06: Phase 2 source inspection and lossless staging

- **Concrete contributions:** Read project rules and all docs; applied Ponytail's existing-library/standard-library approach; inspected current available inputs, compared each XLSX independently, sampled PDF first pages and built versioned CSV ingestion with source/row provenance and separate original/cleaned/derived values. Generated per-column measured dictionary and reassessed detector feasibility. No dashboard, detector or risk score implemented.
- **Sources:** Nine supplied files exist for expenditure, sanctioned and completed reports. Copies under data/raw match all Downloads hashes. The first copy attempt encountered missing allocation/calamity files; its unconditional success message was invalid. A separate stop-on-error verification confirmed exactly nine available copy pairs, not fifteen. No missing file was reconstructed. PDF first pages show clipped right columns; no PDF data ingested.
- **Data result:** 34,000 CSV detail rows plus three retained summary rows. No malformed-width rows or invalid numeric/date values in these available CSVs. Four completed disbursal values missing and 2,658 Image N/A markers. Expenditure contains 143 exact repeated detail rows ignoring serial, all preserved. All three totals fail reconciliation; coverage remains unverified. Workbook counts and raw text differences are recorded, not silently merged.
- **Files created:** `backend/src/backend/ingest.py`, `backend/src/backend/inspect_exports.py`, `backend/src/backend/staging.py`, three files under `backend/tests/`, `docs/ingestion.md`; local raw copies, ignored processing output and PDF preview files.
- **Files modified:** `.gitignore`, `.env.example`, `backend/pyproject.toml`, `backend/uv.lock`, `docs/data-dictionary.md`, `docs/detection-rules.md`, `docs/source-register.md`, `docs/decisions.md`, `docs/flow.md`, `docs/PRD.md`, `docs/architecture.md`, `docs/techstack.md`, `docs/mcp-setup.md`, `docs/CODEX_LOG.md`.
- **Implementation choices:** Exact report contracts; decimal strings for INR; locale-independent date parsing; summary/rejected record retention; derived ID whitespace handling; version/hash-based rerun identity and overwrite refusal. PostgreSQL staging has two tables and explicit parameterised transactional inserts. No inferred project schema or automatic deduplication. Batch validation does not activate risk flags.
- **Dependency issue and resolution:** Existing Psycopg import failed with no pq wrapper / libpq missing. Consulted current Context7 documentation, then `uv add 'psycopg[binary]>=3.3.5'` resolved the driver through psycopg-binary 3.3.5. No database server installed. Spreadsheet authoring runtime unavailable; analysis used standard-library CSV and bounded static XLSX XML inspection, without workbook authoring. Existing Poppler used for PDFs.
- **Tests:** `uv run --frozen pytest -q`: 28 passed, one live PostgreSQL test skipped because TEST_DATABASE_URL is absent. Covers raw preservation, deterministic reruns, footer handling, multiline provenance, malformed rows, missing/invalid amounts/dates, unknown status, ID failure, duplicate retention, output protection, exact monetary strings, XLSX sparse cells/unsupported formulas/entities, parameterised staging and idempotency/conflict contracts. Mock SQL tests are not a substitute for database verification.
- **Other checks:** Ruff formatting and `ruff check --no-cache` passed. Initial Ruff cache-write warning was avoided using no-cache. Real-data inspection rerun produced identical hashes for every generated output. All nine original/copy hashes match. Git ignore rules cover raw and processed data. No commits or pushes.
- **Current limitations:** PostgreSQL service and DATABASE_URL/TEST_DATABASE_URL absent; live persistence, transaction rollback and schema compatibility still unverified. Source coverage/filters and missing source sets need review. CSV-only ingestion and bounded static-XLSX inspection are intentional. No browser/accessibility tests run because no UI changed. No large-scale performance or fraud-detection claims.
- **Manual actions and acceptance:** Configure a dedicated test PostgreSQL connection via environment, verify the live integration test, restore missing allocation/calamity files if needed and confirm export coverage. Stopped before detector/UI development; do not call the full phase complete yet.

## 2026-09-06: Expanded brief, repository inspection and initial source research

- **Concrete contributions:** Read the latest attached brief, root rules and all existing project documentation. Inspected the authored repository tree, frontend source/configuration, backend entry points and dependency declarations. Confirmed empty `data/` and absent `data/raw/`. Consulted the already installed Ponytail skill and retained the minimal existing architecture without speculative code.
- **Research:** Official SIH statement fetch returned HTTP 403. A clearly unofficial archive provided a link to the accessible official eSAKSHI dashboard. Inspected its process guidance and selectors; obtained no row-level export. Legacy report fetches returned tool Internal Error. Recorded exact access limitations, source roles and reporting caveats in the source register. No official SIH statement or current clause-level guidelines have been independently verified.
- **Files created:** `docs/PRD.md`, `docs/techstack.md`, `docs/architecture.md`, `docs/data-dictionary.md`, `docs/detection-rules.md`, `docs/source-register.md`.
- **Files modified:** `docs/decisions.md`, `docs/flow.md`, `docs/CODEX_LOG.md`.
- **Important choices:** Latest phase sequence adopted explicitly. Data dictionary is a blocker inventory, not fabricated field statistics. Seven proposed detectors are NOT SUPPORTED against currently available local inputs, with missing evidence documented. Architecture contracts are planned, not claimed as implemented. No dependencies, MCP configurations or application code changed.
- **Tests executed:** `uv run --frozen pytest` in `backend/` on Python 3.12.14 and pytest 9.1.1. PowerShell checks for all nine requested documents, em dashes and replacement characters. Reviewed documented current call flow against source.
- **Results:** Pytest collected 0 items and the command runner returned exit code 1; this is not a passing suite. Documentation existence/punctuation checks passed. No new business logic exists to unit-test. Browser, accessibility, persistence and performance tests were not run, and no claims are made for those areas.
- **Human action required:** Supply the unchanged authorised dataset under `data/raw/` with source and coverage metadata, and an official SIH26102 statement export or accessible official link. Applicable guideline text and amendments must be verified before compliance rules are activated.
- **Known limitations:** Phase 0 is partial and Phase 1 field analysis remains blocked. No database ingestion, measured data dictionary, active detector, risk aggregation, investigation workflow or product UI exists. The six previously missing documents now exist, but they do not resolve the missing data. Existing untracked user files were preserved.

## 2026-09-06

- Added project-scoped Codex MCP configuration for remote Context7 and pinned Playwright.
- Added a disabled, credential-gated Google Stitch MCP configuration for optional UI/UX exploration.
- Deferred GitHub MCP because no GitHub remote exists.
- Added project instructions covering MCP usage, browser QA, non-destructive operation and MPLADS risk-system safeguards.
- Added secret-safe environment variable guidance and ignore rules.
- Added MCP setup and decision documentation.
- Verified that Codex parses all three project entries and applies the Playwright unsafe-tool deny list.
- Completed a live Context7 MCP initialisation handshake. The server reported version 4.0.5.
- Listed the Playwright MCP tool catalogue and used `browser_navigate` to open the existing Next.js route at `http://localhost:3000` successfully.
- Reached the official Stitch MCP endpoint and listed its tools without creating or modifying remote data. The project entry remains disabled until `STITCH_API_KEY` is supplied.

### Permanent development rules

- **Task:** Established mandatory repository-wide product, engineering, safety, testing and documentation rules for SIH26102.
- **Files created:** `docs/flow.md`.
- **Files modified:** `AGENTS.md`, `docs/decisions.md`, `docs/CODEX_LOG.md`.
- **Implementation decisions:** Root `AGENTS.md` is the permanent policy source. Documentation must distinguish implemented behaviour from planned behaviour. Generative AI is excluded from risk decisions, and risk results require provenance and explanations.
- **Tests executed:** Inspected the actual Next.js and FastAPI entry points; checked the documentation files for prohibited em dashes and replacement-character encoding; reviewed the documented call flow against the source files.
- **Test results:** Documentation-only change. The recorded frontend and backend call flows match the current scaffold. No application runtime or dependency changed, so application tests were not required for this session.
- **Known limitations:** The frontend is still the create-next-app starter. Authentication, data ingestion, detectors, risk aggregation, PostgreSQL persistence and the review workflow are not implemented.
- **Manual review required:** Review the permanent rules before the first major feature session.
- **Unresolved issues:** The required product documents `docs/PRD.md`, `docs/techstack.md`, `docs/architecture.md`, `docs/data-dictionary.md`, `docs/detection-rules.md` and `docs/source-register.md` do not yet exist and must be created when their content can reflect real agreed requirements or implementation.

### Phase 2 dataset inspection blocked

- **Task:** Install Ponytail and start Phase 2 dataset inspection and ingestion.
- **Files created:** None.
- **Files modified:** `docs/CODEX_LOG.md` only.
- **Implementation decisions:** No ingestion schema, cleaning rule or detector classification was created because `data/raw` is absent and `data/` is empty. Creating them without source fields would fabricate the dataset contract.
- **Tests executed:** `uv run pytest` from `backend/` using Python 3.12.14 and pytest 9.1.1.
- **Test results:** Pytest collected zero tests and exited with code 1. No Phase 2 code exists to test.
- **Known limitations:** Field meanings, datatypes, null rates, unique values, examples, anomaly usefulness and quality concerns cannot be measured without the source dataset.
- **Manual review required:** Place the unchanged MPLADS source dataset in `data/raw/` and rerun Phase 2.
- **Unresolved issues:** `docs/data-dictionary.md`, `docs/detection-rules.md`, the ingestion pipeline, cleaned output and automated ingestion tests remain blocked by the missing source dataset.
