# Frontend feature connections

Updated 2026-09-07. This table records implemented behaviour only.

| UI feature | Frontend component | API endpoint | Backend handler | Data source | Status |
| --- | --- | --- | --- | --- | --- |
| Root route | `app/page.tsx` | Not applicable | Not applicable | Next.js router | Fully functional |
<<<<<<< HEAD
| Suchak AI identity | `Brand`, layout metadata, shared shell and login | Static local PNG | None | Unchanged user-supplied logo | Implemented across existing routes |
| Review distribution and workload links | `ReviewOverview` | Existing investigation summary; filtered queue navigation | Existing summary/list handlers | Actual latest review states | No illustrative analytics values |
| Pair location map | `LocationComparison`, `LocationMapCanvas` | Local `/maps/india.geojson`; optional OSM tiles | None | Verified coordinates from existing candidate source records | India/fit/zoom, keyboard pins, distinct pair selection, missing/failed map states |
| Review Audit Trail | `app/audit-trail/page.tsx` | `GET /review-events` | `list_review_events()` | Existing append-only `mplads_review_event` rows joined to current detector evidence | Protected, server-filtered, paginated, responsive; not represented as a statutory ledger |
| Click-to-fetch source details | `LocationComparison`, `[id]/source/route.ts` | `GET /investigation-queue/[id]/source?sha=...&parser=...&record=...` -> existing protected candidate API | Existing `candidate_detail()` | Candidate-owned source record | Signed session, identity validation, no-store, retry, expiry and stale-request cancellation |
| Ingestion metrics | `CommandCentrePage`, `Dashboard`, `Metric` | `GET /data-overview` | `data_overview()` -> `read_data_overview()` | PostgreSQL staging tables | Fully functional |
=======
| Ingestion metrics | `CommandCentrePage`, `DataQualityPage`, `DataQualityContent`, `Metric` | `GET /data-overview` | `data_overview()` -> `read_data_overview()` | PostgreSQL staging tables | Fully functional |
>>>>>>> main
| Queue workload status | `CommandCentrePage`, `Dashboard`, `Metric` | `GET /investigation-summary` | `investigation_workload()` -> `investigation_summary()` | Latest reviewable detector run and append-only latest events | Fully functional and authenticated |
| Source report table/cards | `DataQualityContent`, `SourceRows` | `GET /data-overview` | `data_overview()` -> `read_data_overview()` | PostgreSQL staging tables | Fully functional |
| Validation review rail | `DataQualityContent` | `GET /data-overview` | `data_overview()` -> `read_data_overview()` | PostgreSQL validation issue counts | Fully functional |
| Pipeline status rail | `DataQualityContent` | No additional request | Not applicable | Verified implementation state | Fully functional |
| Data Quality navigation | `QueueShell`, `DataQualityPage` | `GET /data-overview` | `data_overview()` -> `read_data_overview()` | Protected `/data-quality` route | Fully functional |
| Retry after data service failure | Command Centre and Data Quality retry links | `GET /data-overview` on rerender | `data_overview()` | PostgreSQL through FastAPI | Fully functional |
| Skip to main content | `CommandCentrePage` skip link | Not applicable | Not applicable | Browser fragment navigation | Fully functional |
<<<<<<< HEAD
| Reviewer sign in/out | `app/login`, shared `QueueShell` | Next.js Server Actions | Signed-cookie helpers | Environment-configured local reviewer | Fully functional for local development; Command Centre and queue protected |
| Password visibility | `PasswordField` | None | None | Local input state only | Show/hide button preserves value and does not submit |
| Sign-in and review pending states | `SubmitButton` | Existing Server Actions | Existing login/review handlers | React form status | Disables submit while pending |
| Evidence summary and desktop reviewer rail | Candidate detail, shared CSS | Existing candidate detail request | `candidate_detail()` | Returned severity, match confidence, record count and distance | Responsive layout; missing distance remains unavailable |
=======
| Reviewer sign in/out | `app/login`, shared `QueueShell` | Next.js Server Actions | Signed-cookie helpers | Environment-configured local reviewer | Fully functional for local development; Command Centre, Data Quality and queue protected |
>>>>>>> main
| Candidate search, state/status filters, sorting and pagination | `InvestigationQueuePage` | `GET /investigation-candidates` | `list_candidates()` | Latest reviewable detector run and review events | Fully functional |
| Candidate evidence and provenance | `app/investigation-queue/[id]` | `GET /investigation-candidates/{result_id}` | `candidate_detail()` | Detector results and staged source records | Fully functional |
| Review status, decision, evidence notes and history | Candidate detail review form | `POST /investigation-candidates/{result_id}/events` | `add_review_event()` | Append-only `mplads_review_event` | Fully functional |
| Route loading state | Command Centre, Data Quality and Investigation Queue `loading.tsx` | Pending route fetch | Not applicable | Next.js route streaming | Browser-tested with delayed synthetic API responses and captured screenshots |
| No-source empty state | `Dashboard` | `GET /data-overview` | `read_data_overview()` | Empty PostgreSQL staging result | Browser-tested with a synthetic empty response; official database remains non-empty |
| Composite scores and project dossier | Not displayed | Missing | Missing | No supported score model or dossier contract | Missing dependency |
| Filtered queue CSV export | `ExportButton`, authenticated export route | `GET /investigation-candidates.csv` | `export_candidates()` | All matching candidates, provenance and latest review details | Fully functional, maximum 10,000 groups |
| Production identity, roles and assignments | Not displayed | Missing | Missing | Approved organisational identity provider unavailable | Missing dependency |

The browser receives server-rendered aggregate data and, after authentication, the selected candidate evidence. PostgreSQL credentials and the review API key remain in server process environments and are not exposed to browser JavaScript.
