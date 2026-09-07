# MPLADS Risk Intelligence and Early Warning System

SIH26102 is an administrative decision-support application for screening supplied MPLADS reports, preserving source evidence and prioritising records that require official verification.

The current deterministic rule found 174 potential-duplicate candidate groups in the supplied All India, Lok Sabha snapshot. These are review candidates, not confirmed duplicates or proof of misuse. Dataset coverage and extraction timing remain unverified.

## Current implementation

- Reproducible CSV inspection, validation and PostgreSQL staging
- Immutable source-row provenance and separate original, cleaned and derived values
- Versioned exact-field potential-duplicate screening
- Authenticated Command Centre and Investigation Queue
- Search, filtering, stable sorting, pagination and formula-safe CSV export
- Append-only review status, evidence notes and decisions
- Pytest, Ruff, ESLint and Playwright coverage

## Repository

- `backend/`: FastAPI, ingestion, detector and PostgreSQL logic
- `frontend/`: Next.js reviewer application and browser tests
- `docs/`: product, data, detector, flow, decisions and operational guidance
- `scripts/`: local PostgreSQL management helper

Official source files and local database state are intentionally excluded from Git.

## Start locally

Follow [Investigation Queue setup](docs/investigation-queue.md). PostgreSQL and ingestion setup are in [docs/ingestion.md](docs/ingestion.md).

Backend checks:

```powershell
cd backend
uv sync --frozen
uv run ruff check src tests
uv run pytest -q
```

Frontend checks:

```powershell
cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e
```

## Deployment

Use [deployment readiness](docs/deployment.md) before staging. The first deployment should be private and access-controlled. Public or departmental production use is blocked until organisational identity, managed PostgreSQL, secure data transfer and operational controls are approved.

Permanent engineering and product safeguards are in [AGENTS.md](AGENTS.md).
