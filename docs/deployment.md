# Deployment readiness

Updated 2026-09-09. The backend and PostgreSQL infrastructure are deployed for staging. The application is not ready for a public or departmental production deployment because the deployed database currently contains no staged source batches or detector results, and the production frontend and identity flow are not verified here.

## Verified staging status

Read-only external checks on 2026-09-09 established the following:

- `https://mplads-risk-intelligent.onrender.com/` returned HTTP 200 with the expected FastAPI service identity.
- `/health` returned HTTP 200 and a healthy status.
- PostgreSQL-backed `/data-overview` returned HTTP 200, confirming that the deployed backend can execute its database request path.
- Protected `/investigation-summary` returned HTTP 401 without `X-MPLADS-Review-Key`, which is the expected minimum-access behaviour.
- `/data-overview` reported zero source batches and zero retained records. The Neon database infrastructure is online, but the six official ingestion batches and reviewable detector run have not yet been verified in the deployed database.

No state-changing endpoint was called during verification. Do not claim that the 141,717 staged records or 174 potential-duplicate groups are live until the deployed endpoints confirm them.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests to `master`, and can also be started manually. It has read-only repository permission and requires no project secret.

- The backend job installs pinned uv 0.12.10 and Python 3.12, checks Ruff formatting and lint, and runs Pytest against an ephemeral PostgreSQL 17 service. Its database credential is generated from the GitHub run ID and is valid only inside that isolated runner.
- The frontend job uses Node.js 22, installs the committed npm lock, runs ESLint, builds the production Next.js application through the existing Playwright web server, and runs the interaction and responsive suites across Chromium, Firefox and WebKit. Optional screenshot generation is described in [responsive-ui.md](responsive-ui.md).

Action dependencies are pinned to commit hashes. CI validates the repository only. It has no deployment, database administration, issue, pull-request merge or branch mutation permission.

## Intended runtime shape

## Evaluated staging targets

A hybrid staging target is defined and partly verified:
- **Frontend:** Next.js 16 deployed to **Cloudflare Workers / Pages** using `@opennextjs/cloudflare` with `nodejs_compat`. Configuration is in `frontend/wrangler.jsonc` and `frontend/open-next.config.ts`.
- **Backend:** FastAPI is deployed to **Render**. The public root and health endpoints are responding.
- **Database:** PostgreSQL is deployed on **Neon** and is reachable through the backend. The deployed database is currently empty according to `/data-overview`.
- **Complete guide:** Refer to [docs/cloudflare-render-deployment.md](cloudflare-render-deployment.md).

```text
HTTPS (Public Internet)
-> Cloudflare Edge (Next.js SSR via OpenNext)
-> Server-to-Server HTTPS (with X-MPLADS-Review-Key)
-> FastAPI backend (Render Web Service)
-> PostgreSQL (Neon, encrypted TLS)
```

Use one instance of each service for staging. The browser reaches only the Cloudflare-hosted Next.js frontend. Next.js performs server-to-server FastAPI requests, so the review API key and database connection never enter browser JavaScript.

## Required services and commands

PostgreSQL must be provisioned before the applications. Create owner/application roles and tables using the authorised setup described in [ingestion.md](ingestion.md) or the idempotent utility `uv run python -m backend.init_db`, then transfer and ingest official source files through an approved secure process. Raw government exports and database credentials must not be committed to Git or baked into an image.

Backend build and start:

```text
uv sync --frozen --no-dev
uv run --frozen uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Frontend build and start:

```text
npm ci
npm run build
npm run start -- --hostname 0.0.0.0 --port 3000
```

The official Next.js 16 self-hosting guide recommends a reverse proxy. Runtime server-only environment variables are supported. Standalone build output is available but has not been enabled because the hosting format is undecided.

## Runtime environment

Backend:

- `DATABASE_URL`: production PostgreSQL connection using TLS and the least-privilege application role
- `MPLADS_REVIEW_API_KEY`: strong secret shared only with the Next.js server

Frontend:

- `MPLADS_API_BASE_URL`: private backend URL
- `MPLADS_REVIEW_API_KEY`: same server-to-server secret
- `MPLADS_REVIEW_USERNAME`: staging-only reviewer name
- `MPLADS_REVIEW_PASSWORD`: staging-only strong password
- `MPLADS_SESSION_SECRET`: independent random secret of at least 32 bytes
- `MPLADS_SECURE_COOKIES=true`
- `NODE_ENV=production`

Do not prefix secrets with `NEXT_PUBLIC_`. For multiple Next.js instances, also configure the documented shared Server Action encryption key and deployment/version-skew controls. That complexity is unnecessary for the first single-instance staging deployment.

## Release gates

Before private staging:

1. Select a hosting target, region and data-handling policy.
2. Push the CI workflow, confirm both jobs pass in GitHub Actions, then require the `Backend` and `Frontend` checks in the agreed branch policy before team development.
3. Provision private PostgreSQL with TLS, backups, restore testing and separate application/administration credentials.
4. Enter secrets through the hosting platform, never through repository files or build logs.
5. Load official data securely and verify source hashes, record counts, the 174 current candidate groups and zero unintended review events.
6. Run Ruff, Pytest, ESLint, the production Next.js build and Playwright against the staging URL.
7. Confirm HTTPS cookies, backend network isolation, error logs without secrets, download handling and a rollback procedure.

Before production:

1. Replace the single local reviewer account with the approved organisational identity provider and role mapping.
2. Define authorised users, audit-log retention, session policy, data classification, export controls and incident response.
3. Approve database backup/restore, monitoring, patching, vulnerability review and availability requirements.
4. Complete accessibility, performance and security testing on the selected infrastructure.
5. Obtain formal approval for the dataset scope, detector wording and operational use. Potential duplicate candidates must never be presented as confirmed misuse.

## Current status
- Cloudflare and Render deployment configuration is defined (`render.yaml`, `frontend/wrangler.jsonc`, `frontend/open-next.config.ts`, `docs/cloudflare-render-deployment.md`).
- Schema initialisation utility is implemented (`backend/src/backend/init_db.py`).
- Staging deployment can be initiated following the operational guide. Production identity, role requirements, and formal audit approvals remain required before wider access.
