# Technology baseline

Inspected 2026-09-06. Manifest declarations are not claims of runtime verification.

| Area | Present in repository | Intended use / limitation |
| --- | --- | --- |
| Frontend | Next.js 16.3.4, React 19.2.8, TypeScript 5, Tailwind 4 | Command centre and authenticated Investigation Queue with review actions and CSV export |
| Backend | FastAPI, Uvicorn, Pydantic | Status, aggregate data, protected candidate/evidence, review-event and CSV endpoints |
| Python | Python 3.12 selection, uv, uv.lock | Use uv and the committed lock for reproducibility; pyproject currently permits Python >=3.12 |
| Analytics | pandas, NumPy, scikit-learn declared | Active deterministic potential-duplicate rule uses the standard library; no trained ML model |
| Persistence | PostgreSQL 17.11 and psycopg[binary] | Project-local loopback service; two-table staging verified; SQLAlchemy remains declared but unused |
| Backend quality | pytest and Ruff | 50 tests pass against the configured dedicated test database; Ruff passes |
| Frontend quality | ESLint and production build | Both pass; no Vitest dependency added for the current server-rendered slice |
| Browser QA | Playwright MCP plus pinned `@playwright/test` | MCP verified the live Investigation Queue in Chromium at the permitted origin. The reproducible E2E suite covers Chromium, Firefox and WebKit, including authentication, filters, pagination, evidence, review history, keyboard use and phone/tablet layouts |
| Continuous integration | GitHub Actions | Two read-only jobs reproduce backend PostgreSQL integration checks and frontend production-build browser QA on pushes and pull requests to `master`; no deployment permission or project secret |
| Responsive screenshots | Existing Playwright and Node.js | Eight viewport sizes, additional 640-pixel reflow check, loading/error/empty/review states and an optional local PNG gallery; see [responsive-ui.md](responsive-ui.md) |

Exact backend ranges are in `backend/pyproject.toml`; resolution is in `backend/uv.lock`. Psycopg's binary extra was added after a verified missing-libpq failure on Windows. Standard-library CSV, Decimal, JSON and hashing implement file staging. Standard-library regular expressions, grouping and median calculation implement deterministic detector screening. Read-only static XLSX inspection uses zipfile/XML, not a general workbook library. Frontend dependencies are unchanged in `frontend/package.json` and `frontend/package-lock.json`. Native Next.js Server Components, `fetch`, semantic HTML and CSS cover this slice without TanStack Table, icon, state or dialog libraries.

Reuse the current stack. Add Zod, text-similarity tooling, Vitest or axe only for a concrete need. No agent framework or additional microservices. Context7 was used before implementing Psycopg transactions, JSONB and binary installation. Poppler was already available for PDF reference inspection.

Ponytail is already available as a development skill/plugin, not a production dependency or MCP server. Apply its minimal-solution guidance without weakening validation, provenance, security, accessibility or tests. MCP status and environment requirements remain in [mcp-setup.md](mcp-setup.md).
