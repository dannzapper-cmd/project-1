# LeadForge controlled deployment guide

This guide covers Block 11A/11B: a cheap, controlled public backend deployment
that lets the Vercel frontend call the FastAPI backend while preserving the
demo/replay safety boundaries.

Recommended shape:

- Frontend: Vercel (existing Next.js deployment).
- Backend: Render Web Service running FastAPI.
- Database: no production database for this block. SQLite schema init remains
  local/ephemeral only and is not used for durable review or pipeline state.
- No Docker, Redis, Postgres, queue workers, full auth, email provider, CRM, or new
  paid APIs are required.

## Why Render for the backend

Render's Python Web Service path supports FastAPI with a simple build command
and start command, including the `$PORT` value Render provides at runtime. This
matches the current backend structure and avoids adding Docker or another
platform layer for Block 11A.

The repository includes a minimal `render.yaml` for the backend service:

```yaml
services:
  - type: web
    name: leadforge-backend
    runtime: python
    plan: free
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
```

You can use the Blueprint or enter the same values manually in Render.

## Backend deployment on Render

### Option A: Render Blueprint from `render.yaml`

1. Open the Render Dashboard.
2. Click **New +**.
3. Click **Blueprint**.
4. Connect the GitHub repository that contains this project.
5. For **Blueprint Path**, enter exactly:
   ```text
   render.yaml
   ```
6. For the service named **leadforge-backend**, enter the required environment
   variable when Render prompts for `CORS_ORIGINS`:
   ```text
   https://YOUR_VERCEL_PROJECT_DOMAIN,http://localhost:3000,http://127.0.0.1:3000
   ```
   Replace `https://YOUR_VERCEL_PROJECT_DOMAIN` with the exact Vercel frontend
   origin, for example `https://leadforge-demo.vercel.app`. Do not include a
   trailing slash.
7. Click **Apply** / **Create Blueprint**.
8. Wait for the first deploy to finish.
9. Open:
   ```text
   https://YOUR_RENDER_SERVICE_NAME.onrender.com/health
   ```
   Expected response includes `"status":"ok"` and `"db":"ok"` or, if the DB
   health check fails, `"status":"degraded"`.

### Option B: manual Render Web Service

1. Open the Render Dashboard.
2. Click **New +**.
3. Click **Web Service**.
4. Select the GitHub repository that contains this project.
5. In **Name**, enter exactly:
   ```text
   leadforge-backend
   ```
6. In **Runtime** or **Language**, select exactly:
   ```text
   Python 3
   ```
7. In **Branch**, select exactly:
   ```text
   main
   ```
8. In **Root Directory**, leave the field empty.
9. In **Build Command**, enter exactly:
   ```text
   pip install -r backend/requirements.txt
   ```
10. In **Start Command**, enter exactly:
    ```text
    cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    ```
11. In **Instance Type**, select exactly:
    ```text
    Free
    ```
12. In **Health Check Path**, enter exactly:
    ```text
    /health
    ```
13. In **Environment Variables**, add these variables:

    | Name | Value |
    |------|-------|
    | `APP_ENV` | `production` |
    | `LOG_LEVEL` | `INFO` |
    | `ENABLE_LIVE_MODEL_PIPELINE` | `false` |
    | `CORS_ORIGINS` | `https://YOUR_VERCEL_PROJECT_DOMAIN,http://localhost:3000,http://127.0.0.1:3000` |

    Replace `https://YOUR_VERCEL_PROJECT_DOMAIN` with the exact Vercel frontend
    origin, for example `https://leadforge-demo.vercel.app`. Do not include a
    trailing slash.
14. Click **Create Web Service**.
15. Wait for deploy logs to show the service has started.
16. Open:
    ```text
    https://YOUR_RENDER_SERVICE_NAME.onrender.com/health
    ```

## Backend environment variables

Required for controlled public deployment:

| Variable | Value | Why |
|----------|-------|-----|
| `APP_ENV` | `production` | Marks the public backend environment and rejects wildcard CORS. |
| `CORS_ORIGINS` | `https://YOUR_VERCEL_PROJECT_DOMAIN,http://localhost:3000,http://127.0.0.1:3000` | Allows the deployed Vercel origin and local development origins. |
| `ENABLE_LIVE_MODEL_PIPELINE` | `false` | Keeps live model calls disabled by default. |

Optional:

| Variable | Default | Why |
|----------|---------|-----|
| `APP_NAME` | `leadforge-backend` | Metadata in `/health`. |
| `APP_VERSION` | `0.1.0` | Metadata in `/health`. |
| `LOG_LEVEL` | `INFO` | Backend log level. |
| `DATABASE_URL` | `sqlite:///./leadforge.db` | Local SQLite schema init only; do not treat as production persistence on Render. |
| `GROQ_API_KEY` | unset | Required only if you intentionally enable the backend-only live Groq endpoint. |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant` | Optional Groq model id for the live endpoint. |
| `GROQ_TIMEOUT_SECONDS` | `30` | Optional Groq request timeout. |
| `ENABLE_LIVE_RESEARCH` | `false` | Block 10E live web research master switch. Off by default. |
| `EXA_API_KEY` | unset | Backend-only Exa key. Never set this as a `NEXT_PUBLIC_*` variable. |
| `LIVE_RESEARCH_MAX_RESULTS` | `3` | Hard cap on Exa results per request. |
| `LIVE_RESEARCH_TIMEOUT_SECONDS` | `8` | Per-request Exa timeout. Block 10E surfaces a structured timeout response when exceeded. |
| `LIVE_RESEARCH_DAILY_LIMIT` | `20` | In-process daily request counter cap; resets on backend restart by design (no Redis/DB persistence). |
| `RATE_LIMIT_ENABLED` | `true` | Block 11B in-memory public-demo rate limiting. Resets on Render restart/spin-down. |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30` | Protected preview/process request cap per IP. |
| `RATE_LIMIT_LIVE_REQUESTS_PER_MINUTE` | `5` | Lower cap for live research, assistant, and Groq-backed paths. |
| `MAX_LEADS_PER_RUN` | `10` | Configurable public-demo intake/process cap. |
| `INTAKE_MAX_UPLOAD_MB` | `5` | Block 11B in-memory CSV/XLSX/PDF intake upload limit. |
| `DEMO_ACCESS_CODE` | unset | Optional portfolio-demo abuse deterrent. If set, protected actions require the `X-LeadForge-Demo-Key` header. |
| `BUILD_SHA` | unset | Optional safe deployment traceability field returned by `/api/system/status`. |

Do not add real secrets to `.env.example`, `render.yaml`, README files, or any
`NEXT_PUBLIC_*` frontend variable.

### Block 10F-A — CSV, Excel, and PDF table intake

Add Leads supports in-memory multipart uploads through
`POST /api/intake/extract-file` for CSV, `.xlsx`, and text-based PDF tables.
The backend uses `openpyxl` for `.xlsx` and `pdfplumber` for PDF text/table
extraction; both are Python libraries listed in `backend/requirements.txt`.
No uploaded files are written to disk or persisted.

Limits and scope:

- Default upload cap is `INTAKE_MAX_UPLOAD_MB=5`.
- Legacy `.xls` is rejected; save as `.xlsx`.
- PDF support is best-effort for text-based tables. Scanned/image PDFs return
  an OCR-needed message because image/OCR intake is out of scope for this block.
- Extracted rows enter the same preview, mapping confirmation, validation, and
  max-10 processing flow as CSV/paste intake.

### Block 10E — Live Web Research (Exa) deployment notes

The Block 10E endpoint at `POST /api/research/live-company` is OFF by default
and is wired into the demo dashboard's lead detail drawer as a manual,
single-lead button labelled "Run live research". To enable it on Render:

1. Set `ENABLE_LIVE_RESEARCH=true`.
2. Set `EXA_API_KEY` to a valid Exa API key in the Render dashboard
   environment configuration.
3. Optionally tune `LIVE_RESEARCH_MAX_RESULTS`, `LIVE_RESEARCH_TIMEOUT_SECONDS`,
   and `LIVE_RESEARCH_DAILY_LIMIT`. The defaults are deliberately low for the
   public demo.

Safety guarantees for this path:

- The Exa API key is never exposed to the frontend. There is no
  `NEXT_PUBLIC_EXA_API_KEY` variable and the response body never contains the
  key.
- The endpoint always returns HTTP 200 with a structured body. Disabled,
  unavailable (no key), rate-limited, timeout, and no-evidence states are
  reported via `status` and `user_message`, not via HTTP error codes.
- Snippets and titles returned by Exa are repackaged into evidence cards
  without any LLM summarization or paraphrasing.
- The daily limit is enforced by an in-process counter that resets on backend
  restart. This block deliberately does not introduce Redis, Postgres, file
  persistence, or background workers.

## Vercel frontend wiring

Add Leads calls the FastAPI backend through `NEXT_PUBLIC_API_URL`. The replay
dashboard can remain in mock mode.

1. Open the Vercel Dashboard.
2. Select the LeadForge project.
3. Click **Settings**.
4. Click **Environment Variables**.
5. In **Name**, enter exactly:
   ```text
   NEXT_PUBLIC_API_URL
   ```
6. In **Value**, enter exactly:
   ```text
   https://YOUR_RENDER_SERVICE_NAME.onrender.com
   ```
   Replace the placeholder with the Render backend base URL. Do not include a
   trailing slash.
7. In **Environment**, select **Production**. Also select **Preview** if branch
   preview deployments should call the same backend.
8. Click **Save**.
9. Trigger a new Vercel deployment. Environment variable changes do not apply
   to already-built deployments.

Optional:

- Keep `NEXT_PUBLIC_DATA_SOURCE=mock` for the safest public replay dashboard.
- Set `NEXT_PUBLIC_DATA_SOURCE=api` only if you want the sample dashboard data
  itself to load from the backend. Add Leads does not require changing this
  variable.

Never put secrets in `NEXT_PUBLIC_*` variables. They are bundled for browser
access by design.

## CORS behavior

The backend reads `CORS_ORIGINS` as a comma-separated list.

Example:

```text
CORS_ORIGINS=https://leadforge-demo.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

Behavior:

- Default local development origin: `http://localhost:3000`.
- Production rejects wildcard `*` origins at startup.
- Origins are exact browser origins: scheme + host + optional port, no path,
  no trailing slash.
- Allowed methods are `GET`, `POST`, and `OPTIONS`.
- The frontend client uses `credentials: "omit"` and the backend does not set
  cookies for the demo API.

If Vercel shows a CORS error, update `CORS_ORIGINS` in Render, redeploy the
backend, then redeploy Vercel if `NEXT_PUBLIC_API_URL` also changed.

## Health check

Public health URL:

```text
https://YOUR_RENDER_SERVICE_NAME.onrender.com/health
```

Expected success:

```json
{
  "status": "ok",
  "app": "leadforge-backend",
  "version": "0.1.0",
  "env": "production",
  "db": "ok"
}
```

Safe status URL:

```text
https://YOUR_RENDER_SERVICE_NAME.onrender.com/api/system/status
```

This endpoint exposes only safe booleans and deployment hints such as
`rate_limit_enabled`, live feature configured true/false, `storage_mode:
"ephemeral"`, and optional `build_sha`. It never exposes API keys, secret env
values, internal paths, or provider credentials.

## Free hosting limitations

Render Free web services are useful for a controlled public preview, but they
are not equivalent to paid hosting for live demos:

- Free services spin down after about 15 minutes without inbound traffic.
- The next request spins the service back up and can take about 50 seconds to
  about one minute.
- Render Free services use an ephemeral filesystem. Local file changes,
  including local SQLite database files, can be lost on redeploy, restart, or
  spin-down.
- Do not add fake uptime pings or keepalive jobs for this block.

Optional upgrade: Render's cheapest paid web service instance (commonly the
Starter plan, about $7/month as of the 2024-2025 pricing era) avoids free-tier
spin-down. Treat this as optional for smoother demos, not required for Block
11A.

## SQLite warning for Render

The backend currently initializes a SQLite schema on startup. In this product
state, pipeline runs, review decisions, telemetry history, and exports are not
durably persisted as production data.

On Render Free or Starter without a persistent disk, SQLite files live on an
ephemeral filesystem. Any SQLite writes can disappear on redeploy, restart, or
spin-down without a data-recovery path. Do not use this SQLite database as a
production persistence layer.

Do not add a Render disk, Postgres, or migration system for Block 11A. Durable
storage belongs to a later backend deployment block.

## Safety boundaries verified for this deployment

- `/health` is public and lightweight.
- `/api/system/status` is public but safe; it exposes booleans, not secrets.
- Replay/mock demo works without the backend.
- Add Leads requires the backend for preview/process.
- CSV/XLSX/text-PDF upload is capped by `INTAKE_MAX_UPLOAD_MB` (default 5 MB).
- User-lead batch processing is capped by `MAX_LEADS_PER_RUN` (default 10).
- Protected demo actions are rate limited in memory by IP. Counters reset on
  Render restart/spin-down by design.
- If `DEMO_ACCESS_CODE` is set, protected demo actions require the
  `X-LeadForge-Demo-Key` header. This is abuse deterrence, not full auth.
- Deterministic and intake routes do not require API keys.
- Live Groq/model routes are backend-only, single-lead, opt-in, and guarded by
  `ENABLE_LIVE_MODEL_PIPELINE=true` plus `GROQ_API_KEY`.
- App startup does not require Groq or other model keys.
- No email sending is implemented.
- No CRM writes are implemented.
- Live web research (Block 10E, Exa) is OFF by default. When enabled it is
  manual, single-lead-only, backend-keyed, daily-limited via an in-process
  counter, and never routed through Groq or any LLM.
- Contextual LLM lead assistant (Block 10G) is OFF by default. When enabled
  it is manual-trigger only, single-selected-lead only, backend-keyed
  (reuses `GROQ_API_KEY` and `GROQ_DEFAULT_MODEL` — no parallel assistant
  API key), and bounded by an in-process daily counter
  (`LLM_ASSISTANT_DAILY_LIMIT`, default 30) plus a per-IP sliding window
  (`LLM_ASSISTANT_PER_IP_LIMIT`, default 5 per 10 minutes). The assistant
  never browses the web, sends email, writes to a CRM, or triggers live
  research. Question length is capped by
  `LLM_ASSISTANT_MAX_QUESTION_CHARS` (default 300). The system prompt is
  constructed backend-side and is never exposed in any response field.
- No full auth, payments, Redis, queue workers, or other paid search APIs
  are introduced by this deployment path.
- Request logs include request id, endpoint, method, status, latency, and a
  high-level error category. They do not log secrets, prompts, uploaded file
  contents, API keys, or private contact data.

## Troubleshooting

### Failed to fetch

Likely causes:

1. `NEXT_PUBLIC_API_URL` is missing in Vercel.
2. `NEXT_PUBLIC_API_URL` points to the wrong Render URL.
3. The Render service is sleeping or failed to deploy.

Fix:

1. Open Vercel **Settings** -> **Environment Variables**.
2. Confirm `NEXT_PUBLIC_API_URL` equals:
   ```text
   https://YOUR_RENDER_SERVICE_NAME.onrender.com
   ```
3. Redeploy Vercel.
4. Open the backend health URL directly and wait for cold start if needed.

### CORS error

Likely cause: Render `CORS_ORIGINS` does not include the exact Vercel origin.

Fix:

1. Open Render service **Environment** settings.
2. Set `CORS_ORIGINS` to:
   ```text
   https://YOUR_VERCEL_PROJECT_DOMAIN,http://localhost:3000,http://127.0.0.1:3000
   ```
3. Redeploy the Render service.

### Backend sleeping or cold start

On Render Free, the first request after inactivity can take about 50 seconds to
about one minute. Open `/health`, wait for the response, then retry Add Leads.
For public demos where delay is unacceptable, upgrade the backend to the
cheapest paid Render web service instance.

### Missing `NEXT_PUBLIC_API_URL`

Add the variable in Vercel and redeploy. Existing Vercel deployments do not
receive newly added environment variables until a new deployment is built.

### 422 validation errors

HTTP 422 from `/api/intake/preview` or `/api/demo/pipeline/batch` usually means
the submitted lead data is invalid, not that deployment is broken. Check
required fields:

- `company_name`
- `industry`

Also confirm the UI's detected column mapping before processing.
