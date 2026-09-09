# Cloudflare and Render deployment guide

This operational guide describes deploying the MPLADS Risk Intelligence System using Cloudflare for the Next.js frontend and Render for the FastAPI backend and managed PostgreSQL database.

## Architecture

```text
[Browser / Official]
        │
        ▼ (HTTPS)
[Cloudflare Edge Network]
  └── Next.js 16 SSR (Cloudflare Workers / Pages via @opennextjs/cloudflare)
        │
        ▼ (Server-to-Server HTTPS with X-MPLADS-Review-Key)
[Render Web Service]
  └── FastAPI backend (Python 3.12, Uvicorn, uv)
        │
        ▼ (Encrypted TLS PostgreSQL connection)
[Render Managed PostgreSQL]
  └── Staged MPLADS batches, detector runs, and review audit trail
```

### Key characteristics

1. **Security boundary:** The browser interacts exclusively with the Cloudflare-hosted Next.js frontend. Database credentials and the `X-MPLADS-Review-Key` secret remain strictly on the server and are never included in client JavaScript bundles.
2. **Global distribution:** Next.js Server Components and server-rendered routes run on Cloudflare Workers with built-in DDoS mitigation and TLS termination.
3. **Data provenance:** Raw government files (`data/raw/`) and local database state remain uncommitted. Staging and screening are executed securely over TLS from an authorised administrative workstation into the Render database.
4. **Cost efficiency:** Cloudflare Pages/Workers provides extensive free request allowances, while Render provides a free tier for one web service and one PostgreSQL instance.

---

## Phase 1: Provision backend and database on Render

### Method A: Deploy using Render Blueprint (Recommended)

1. Sign in to [Render](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your repository (`MPLADS-RISK-INTELLIGENT-`).
4. Render detects `render.yaml` at the root and plans two resources:
   - `mplads-db`: PostgreSQL database (`mplads`, user `mplads_app`).
   - `mplads-api`: Web Service with Python 3.12, `uv sync --frozen --no-dev`, and `healthCheckPath: /health`.
5. Render automatically generates a secure random value for `MPLADS_REVIEW_API_KEY` and injects the database connection into `DATABASE_URL`.
6. Click **Apply**.
7. Once deployed, copy your backend URL (for example: `https://mplads-api.onrender.com`) and your auto-generated `MPLADS_REVIEW_API_KEY` from the `mplads-api` Environment tab.

### Method B: Manual setup via Render Dashboard

If configuring without Blueprints:

1. **Database:**
   - Click **New +** -> **PostgreSQL**.
   - Name: `mplads-db`, Database: `mplads`, User: `mplads_app`, Region: Oregon (or your chosen region).
   - Create Database.
2. **Backend Web Service:**
   - Click **New +** -> **Web Service**.
   - Connect the repository.
   - Name: `mplads-api`, Language: `Python`, Region: same as database.
   - Root Directory: `backend`.
   - Build Command: `uv sync --frozen --no-dev`.
   - Start Command: `uv run --frozen uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
   - Health Check Path: `/health`.
   - Environment Variables:
     - `DATABASE_URL`: paste the **Internal Database URL** from `mplads-db`.
     - `MPLADS_REVIEW_API_KEY`: generate and set a strong random secret (32+ characters).
   - Click **Create Web Service**.

---

## Phase 2: Initialise database schema

The application relies on least-privilege routine execution and does not create tables dynamically at request time. Run the idempotent initialisation script from your local workstation using the Render database **External Connection String**:

1. In the Render Dashboard, navigate to `mplads-db` and copy the **External Database URL**.
2. From the `backend` directory on your workstation:

```powershell
cd backend
$env:DATABASE_URL="postgres://mplads_app:<PASSWORD>@<HOST>.oregon-postgres.render.com/mplads"
uv run --frozen python -m backend.init_db
```

This creates the five required tables and indexes:
- `mplads_ingest_batch`
- `mplads_source_record`
- `mplads_detector_run`
- `mplads_detector_result`
- `mplads_review_event`

---

## Phase 3: Stage official data and run screening

To populate the staging tables and create the reviewable potential-duplicate detector run:

1. Stage the official sanctioned works export:

```powershell
uv run --frozen python -m backend.staging "../data/raw/Works Sanctioned.csv"
```

2. Optionally stage additional verified CSVs (completed works, expenditure):

```powershell
uv run --frozen python -m backend.staging "../data/raw/Works Completed.csv"
uv run --frozen python -m backend.staging "../data/raw/Expenditure.csv"
```

3. Execute the deterministic potential-duplicate detector:

```powershell
uv run --frozen python -m backend.detectors
```

4. Verify that the detector run outputs a JSON summary showing `run_id`, `result_count: 174`, and `stored: true`.

---

## Phase 4: Deploy frontend to Cloudflare

### Method A: Cloudflare Dashboard Git integration (Recommended)

1. Sign in to the [Cloudflare Dashboard](https://dash.cloudflare.com).
2. Navigate to **Compute (Workers & Pages)** -> **Create application** -> **Pages** -> **Connect to Git**.
3. Select your GitHub repository.
4. Set up the build configuration:
   - **Framework preset:** `Next.js`
   - **Root directory:** `frontend`
   - **Build command:** `npx @opennextjs/cloudflare build`
   - **Build output directory:** `.open-next/assets`
5. Under **Environment variables**, configure:
   - `NODE_VERSION`: `22`
   - `MPLADS_API_BASE_URL`: your Render backend URL (e.g. `https://mplads-api.onrender.com`)
   - `MPLADS_REVIEW_API_KEY`: exact matching key from Render `mplads-api`
   - `MPLADS_REVIEW_USERNAME`: your administrative reviewer username
   - `MPLADS_REVIEW_PASSWORD`: a unique strong password
   - `MPLADS_SESSION_SECRET`: a random secret string of at least 32 bytes
   - `MPLADS_SECURE_COOKIES`: `true`
   - `MPLADS_API_TIMEOUT_MS`: `45000` (handles Render free-tier cold starts)
6. Under **Settings** -> **Functions** -> **Compatibility flags**, ensure:
   - **Compatibility date:** `2024-12-30` or later
   - **Compatibility flags:** `nodejs_compat`
7. Click **Save and Deploy**.

### Method B: Deploy via Wrangler CLI

From the `frontend` directory:

1. Authenticate with Cloudflare:
   ```powershell
   cd frontend
   npx wrangler login
   ```
2. Build the worker bundle:
   ```powershell
   npm run build:worker
   ```
3. Set production secrets on Cloudflare:
   ```powershell
   npx wrangler secret put MPLADS_API_BASE_URL
   npx wrangler secret put MPLADS_REVIEW_API_KEY
   npx wrangler secret put MPLADS_REVIEW_USERNAME
   npx wrangler secret put MPLADS_REVIEW_PASSWORD
   npx wrangler secret put MPLADS_SESSION_SECRET
   ```
4. Deploy the application:
   ```powershell
   npm run deploy
   ```

---

## Phase 5: Verification and smoke testing

1. **Backend health check:**
   Visit `https://<your-render-backend>.onrender.com/health`.
   Confirm response: `{"status": "healthy"}`.
2. **Backend data overview:**
   Visit `https://<your-render-backend>.onrender.com/data-overview`.
   Confirm the source batch statistics and record totals are displayed.
3. **Frontend access:**
   Open your Cloudflare URL (e.g. `https://mplads-risk-intelligence.pages.dev`).
4. **Authentication:**
   Sign in with `MPLADS_REVIEW_USERNAME` and `MPLADS_REVIEW_PASSWORD`.
5. **Command Centre:**
   Verify that the candidate counts, New counts, and data readiness metrics appear correctly.
6. **Investigation Queue:**
   Open the queue, test filtering by State, verify pagination, and inspect a candidate detail view.
7. **Review transition:**
   Submit an audit note on a candidate and confirm the event is persisted without altering detector flags.
8. **Export:**
   Download the filtered CSV and confirm that formula protection and source provenance are intact.

---

## Operational notes and limitations

- **Render free tier sleep:** Free Render web services spin down after 15 minutes of inactivity. Cloudflare requests will wait up to 45 seconds (`MPLADS_API_TIMEOUT_MS`) for the service to wake up. For zero-downtime staging demonstrations, consider upgrading the web service to Render Starter ($7/month).
- **Database retention:** Free Render PostgreSQL databases expire after 30 days. Maintain workstation backups or use a persistent plan for long-running staging environments.
- **Audit retention:** All review decisions in `mplads_review_event` are append-only. Do not truncate this table during routine operations.
