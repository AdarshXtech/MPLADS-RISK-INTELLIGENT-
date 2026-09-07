# Backend

FastAPI and Python 3.12 provide data inspection, lossless PostgreSQL staging, deterministic detector execution and the authenticated investigation API.

Use uv for every Python and dependency operation:

```powershell
uv sync --frozen
uv run ruff check src tests
uv run pytest -q
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

`DATABASE_URL` is required for database-backed runtime routes. `TEST_DATABASE_URL` must point only to the dedicated disposable test database. The protected investigation routes also require `MPLADS_REVIEW_API_KEY`.

See [ingestion](../docs/ingestion.md), [detector rules](../docs/detection-rules.md) and [deployment readiness](../docs/deployment.md). Never commit source exports or credentials.
