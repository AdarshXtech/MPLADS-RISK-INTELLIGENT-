# Investigation Queue: local setup and use

Updated 2026-09-07. This is local-development reviewer access, not production organisational authentication.

## Setup

This workstation already has staged data, detector results and the review table. Do not recreate or re-import them just to open the queue. Other workstations should first follow [ingestion setup](ingestion.md).

Set these variables in the environments launching the processes. Use a secret manager or secure environment-variable entry. Do not put secret values in source files, documentation, chat, commits or shared command history.

| Variable | Process | Required value |
| --- | --- | --- |
| `DATABASE_URL` | Backend | Existing least-privilege application connection |
| `MPLADS_REVIEW_API_KEY` | Both | The same strong random secret |
| `MPLADS_API_BASE_URL` | Frontend | `http://127.0.0.1:8000` locally |
| `MPLADS_REVIEW_USERNAME` | Frontend | Your chosen reviewer username |
| `MPLADS_REVIEW_PASSWORD` | Frontend | A unique strong password |
| `MPLADS_SESSION_SECRET` | Frontend | A separate random secret of at least 32 bytes |

Export requires no new variable. Restart processes after changing their environment. No shared default login is provided.

From `backend`, start the API:

```powershell
uv sync --frozen
uv run --frozen uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

From `frontend`, in another terminal:

```powershell
npm ci
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000` and sign in. The Command Centre shows the current review workload; open the queue from there. Keep the same hostname throughout. Development sessions support local HTTP. For `npm run start` over local HTTP only, set `MPLADS_SECURE_COOKIES=false` in that frontend process. Production requires HTTPS, secure cookies and approved organisational identity before wider use. See [deployment readiness](deployment.md).

## Review and download

1. Apply search, state or review-status filters and choose an order. Search matches literal text in evidence JSON, including field names, ignoring case. Available orders are smallest groups, largest groups, State A to Z and most recently reviewed. Candidate ID provides stable ordering when values tie.
2. Open **Review evidence** and inspect source rows and verification guidance. A candidate is not a confirmed duplicate or proof of misuse.
3. Save only genuine review actions after checking evidence. Closing requires a decision; dismissal also requires a reason. Review actions never change detector flags.
4. Click **Export filtered CSV**. It includes every match, including later pages, in the selected order. Unapplied filter or order edits do not affect the download.

One row represents one candidate group, with summary fields, confidence and its meaning, source references, rule/run identity, verification guidance, limitations and latest review details. Lists/references are JSON within CSV cells. Missing review values stay blank. Formula-like cells receive a protective apostrophe; original data is unchanged. UTF-8 BOM and quoting support spreadsheet import.

Export is read-only, does not include complete event history and does not import spreadsheet edits. Handle downloaded evidence and reviewer notes as sensitive administrative information. No matches produces headers only. Above 10,000 groups, narrow filters; results are never silently truncated. For errors, check the backend/session and retry. Expired sessions require signing in again.

## Verify

From `backend`, with a dedicated disposable `TEST_DATABASE_URL`:

```powershell
uv run ruff check src tests
uv run pytest -q
```

From `frontend`:

```powershell
npm run lint
npm run test:e2e
```

E2E tests build the frontend and use an explicitly synthetic API across Chromium, Firefox and WebKit, never submitting review decisions to official data. If binaries are missing, run `npx playwright install chromium firefox webkit` once. PostgreSQL tests use isolated rollback-only schemas in the dedicated test database.
