# Deployment readiness

Updated 2026-09-08. The application is suitable for local development and an access-controlled staging demonstration. It is not ready for a public or departmental production deployment.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests to `master`, and can also be started manually. It has read-only repository permission and requires no project secret.

- The backend job installs pinned uv 0.12.10 and Python 3.12, checks Ruff formatting and lint, and runs Pytest against an ephemeral PostgreSQL 17 service. Its database credential is generated from the GitHub run ID and is valid only inside that isolated runner.
- The frontend job uses Node.js 22, installs the committed npm lock, runs ESLint, builds the production Next.js application through the existing Playwright web server, and runs all nine tests across Chromium, Firefox and WebKit.

Action dependencies are pinned to commit hashes. CI validates the repository only. It has no deployment, database administration, issue, pull-request merge or branch mutation permission.

## Intended runtime shape

```text
HTTPS reverse proxy
-> Next.js frontend (public entry point)
-> FastAPI backend (private network only)
-> PostgreSQL (private network only, encrypted connection)
```

Use one instance of each application for the first staging deployment. The browser must reach only Next.js. Next.js performs server-to-server FastAPI requests, so the review API key and database connection never enter browser JavaScript. Put a maintained reverse proxy or managed ingress in front of Next.js for TLS, request limits and rate limiting. Do not use a static Next.js export because authentication, cookies, Server Actions and request-time rendering require the Node.js server.

No provider-specific Dockerfile or infrastructure file is committed yet. The hosting target affects health checks, secret injection, networking, persistent database setup and build layout. Add those files only after selecting the target.

## Required services and commands

PostgreSQL must be provisioned before the applications. Create owner/application roles and tables using the authorised setup described in [ingestion.md](ingestion.md), then transfer and ingest official source files through an approved secure process. Raw government exports and database credentials must not be committed to Git or baked into an image.

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

## Current blockers

- Hosting provider, domain, region and budget are not selected.
- The initial baseline is on `origin/master`; the default-branch choice, branch protection and team access policy remain pending.
- Production identity and role requirements are unavailable.
- Production PostgreSQL, backups and secure data transfer are unavailable.
- No staging URL, TLS configuration, monitoring destination or deployment authority has been supplied.

No deployment was performed in this session. Publishing would require infrastructure choices and external state changes that must be approved explicitly.
