# Frontend Design

## 1. Purpose

The frontend is a Next.js 16 App Router application for MPLADS Risk Intelligence administrative review.  
It supports secure reviewer access, operational visibility of staged MPLADS data, and evidence-based handling of potential duplicate anomalies.

The interface is designed to help officials answer:

1. What requires attention now
2. Why a candidate was flagged
3. What evidence supports the flag
4. What verification action should be recorded next

It does not present anomaly flags as confirmed fraud or misuse.

## 2. Technology Stack

- Framework: Next.js 16 (App Router)
- Language: TypeScript
- UI styling: global CSS with Tailwind import base
- Runtime model: server-rendered routes with Server Actions
- Authentication model: signed HTTP-only cookie session
- Test tooling: Playwright (Chromium, Firefox, WebKit), ESLint
- Deployment target: Node.js server or OpenNext for Cloudflare

## 3. Information Architecture

### Route map

- `/`  
  Redirects to `/command-centre`.
- `/login`  
  Reviewer sign-in screen.
- `/command-centre`  
  Operational dashboard for ingestion and investigation workload.
- `/data-quality`  
  Data-readiness and validation issue view using shared dashboard logic.
- `/investigation-queue`  
  Search, filter, sort, paginate and export review candidates.
- `/investigation-queue/[id]`  
  Candidate evidence and review action recording page.
- `/investigation-queue/export`  
  CSV export endpoint for filtered candidate lists.

### Shared shell

`QueueShell` provides:

- Primary navigation
- Session header and sign-out action
- Data-service connection status
- Skip link and consistent workspace layout

## 4. Functional Design

### 4.1 Authentication and access control

- Login uses `MPLADS_REVIEW_USERNAME` and `MPLADS_REVIEW_PASSWORD`.
- Session cookie (`mplads_review_session`) is signed using `MPLADS_SESSION_SECRET`.
- Protected pages call `requireReviewer()` and redirect unauthenticated users to `/login`.
- Sign-out clears the session cookie and redirects to login.

### 4.2 Command Centre and Data Quality

- Both views use `ReviewerDashboard` with a `view` mode.
- Dashboard loads `/data-overview` and, for Command Centre, `/investigation-summary`.
- UI includes:
  - Ingestion metrics
  - Source-level provenance and validation issue rates
  - Investigation workload snapshot
  - Explicit evidence boundaries and interpretation notices
- If backend is unavailable, an error panel with retry action is shown.

### 4.3 Investigation Queue

- Server-side query parameters: `query`, `state`, `status`, `sort`, `page`.
- Candidate list is fetched from `/investigation-candidates`.
- Includes:
  - Filter bar with search and dropdown filters
  - Sort order controls
  - Paginated table/card presentation by viewport
  - CSV export control preserving active filters
- Empty states and service-failure states are explicitly handled.

### 4.4 Candidate Detail and Review Workflow

- Candidate details are loaded from `/investigation-candidates/{id}`.
- Screen sections:
  - Why flagged: detector details, severity, confidence, fields used
  - Verification guidance and known limitations
  - Matched values after normalisation
  - Source record provenance
  - Review action form
  - Review history timeline
- Review updates are posted as append-only events to `/investigation-candidates/{id}/events`.
- Allowed status transitions are constrained by current status.

## 5. Data and API Integration Design

API integration is centralised in `lib/investigations.ts`.

- Base URL resolution: `MPLADS_API_BASE_URL` with safe fallback
- Timeout handling: `MPLADS_API_TIMEOUT_MS`
- Auth header: `X-MPLADS-Review-Key` from `MPLADS_REVIEW_API_KEY`
- Fetch policy: `cache: "no-store"` for live administrative data

Primary frontend API contracts:

- `GET /data-overview`
- `GET /investigation-summary`
- `GET /investigation-candidates`
- `GET /investigation-candidates/{id}`
- `POST /investigation-candidates/{id}/events`
- `GET /investigation-candidates.csv`

## 6. UI and Accessibility Design

- Indian English administrative tone in labels and notices
- Clear distinction between risk indicators and verified findings
- Keyboard-accessible controls and skip-link support
- Visible focus states and minimum target sizes
- Responsive layout strategy:
  - Table view on larger screens
  - Card view on smaller screens
  - Multi-breakpoint grid adaptation for dashboard density
- Reduced-motion and forced-colour mode support

## 7. Error and State Design

The UI consistently supports:

- Loading states (`loading.tsx` screens and skeletons)
- Empty states (no candidates or no source reports)
- Service-failure states (retry guidance)
- Success and error feedback on review form actions

Errors surface actionable user guidance without exposing backend stack traces.

## 8. Security Design

- Server-only modules for credentials and API key usage
- Timing-safe credential comparison
- HMAC-signed session token with expiry
- HTTP-only session cookie and production secure-cookie behaviour
- Secret values are never rendered in the client
- Authentication failure logging avoids credential and cookie leakage

## 9. Testing Design

Quality gates defined in frontend scripts:

- `npm run lint`
- `npm run build`
- `npm run test:e2e`

Playwright e2e coverage includes:

- Investigation queue behaviour
- Responsive behaviour checks
- Synthetic mock API integration
- Cross-browser execution in Chromium, Firefox and WebKit

## 10. Design Constraints and Boundaries

- The frontend displays deterministic anomaly outputs and reviewer workflow states.
- It does not generate or alter detector outcomes through LLMs.
- Data quality warnings are presented separately from risk signals.
- Interface copy avoids legal accusation language and treats all flags as requiring verification.
