# LeadForge operations runbook

Block 11B keeps the public demo controlled without turning it into a SaaS. It
uses Render + Vercel, in-memory safety controls, and manual smoke checks.

## Required backend env vars on Render

| Variable | Recommended value | Notes |
| --- | --- | --- |
| `APP_ENV` | `production` | Rejects wildcard CORS. |
| `LOG_LEVEL` | `INFO` | Request logs are structured JSON lines. |
| `CORS_ORIGINS` | `https://YOUR_VERCEL_DOMAIN,http://localhost:3000,http://127.0.0.1:3000` | Exact origins only, no trailing slash. |
| `RATE_LIMIT_ENABLED` | `true` | In-memory per-IP limiter. Resets on Render restart/spin-down. |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30` | General protected demo actions. |
| `RATE_LIMIT_LIVE_REQUESTS_PER_MINUTE` | `5` | Live research, assistant, and Groq-backed paths. |
| `MAX_LEADS_PER_RUN` | `10` | Public demo intake/process cap. |
| `INTAKE_MAX_UPLOAD_MB` | `5` | CSV/XLSX/text-PDF upload cap. `MAX_UPLOAD_SIZE_MB` is also accepted. |
| `DEMO_ACCESS_CODE` | optional private value | If set, protected demo actions require `X-LeadForge-Demo-Key`. Do not expose in frontend env. |
| `BUILD_SHA` | optional commit SHA | Returned as safe deployment traceability in `/api/system/status`. |

Optional live features:

| Variable | Notes |
| --- | --- |
| `ENABLE_LIVE_RESEARCH=true` + `EXA_API_KEY` | Enables manual Exa research only. Keep `LIVE_RESEARCH_DAILY_LIMIT` low. |
| `ENABLE_LLM_ASSISTANT=true` + `GROQ_API_KEY` | Enables manual contextual assistant only. |
| `ENABLE_LIVE_MODEL_PIPELINE=true` + `GROQ_API_KEY` | API-only single-lead Groq comparison path. |

## Required frontend env vars on Vercel

| Variable | Recommended value | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://YOUR_RENDER_SERVICE.onrender.com` | Backend base URL, no trailing slash. |
| `NEXT_PUBLIC_DATA_SOURCE` | `mock` or `api` | `mock` keeps replay dashboard bundled; Add Leads still uses the backend URL. |

Never set `NEXT_PUBLIC_DEMO_ACCESS_CODE`. The demo access code is entered by the
user at runtime and stored only in `sessionStorage` for the current browser tab.

## Render deployment checks

1. Deploy the backend from the target branch/commit.
2. Open Render logs and confirm startup completes without CORS validation errors.
3. Hit `/health`:
   ```bash
   BACKEND_URL=https://YOUR_RENDER_SERVICE.onrender.com bash scripts/smoke-check.sh
   ```
4. Check safe status:
   ```bash
   curl https://YOUR_RENDER_SERVICE.onrender.com/api/system/status
   ```
   Confirm booleans and `storage_mode:"ephemeral"` look correct. No secrets
   should appear.
5. If Render Free is asleep, wait through the smoke script retry loop. Cold
   start can take 40-60 seconds.

## Vercel deployment checks

1. Confirm `NEXT_PUBLIC_API_URL` points at the Render backend.
2. Confirm no secret or demo access code is configured as `NEXT_PUBLIC_*`.
3. Redeploy Vercel after env changes.
4. In browser DevTools, confirm protected POSTs include
   `X-LeadForge-Demo-Key` only after entering the code in the demo page.
5. Verify CORS preflight if needed:
   ```bash
   BACKEND_URL=https://YOUR_RENDER_SERVICE.onrender.com \
   FRONTEND_ORIGIN=https://YOUR_VERCEL_DOMAIN \
   bash scripts/smoke-check.sh
   ```

## Functional smoke: Add Leads -> Preview -> Process

1. Open `/demo`.
2. If `DEMO_ACCESS_CODE` is set on Render, enter the private code in the
   "Private demo access" panel.
3. In Add Leads, paste sample rows or upload a CSV/XLSX/text-based PDF under
   the configured size cap.
4. Click **Preview Leads**.
5. Confirm mapping and warnings are visible.
6. Click **Process Leads**.
7. Confirm dashboard metrics, agent statuses, results table, and detail drawer
   update from the processed batch.

Expected failure modes:

- Missing/invalid access code: friendly private-code message.
- Too many requests: HTTP 429 friendly rate-limit message.
- Unsupported file type: clear 415 copy.
- Oversized upload: clear 413 copy.

## Functional smoke: assistant and live research

1. Open a lead detail drawer.
2. Click a quick assistant chip; the answer should scroll into view near the
   selected chip.
3. If live assistant is enabled, enter a custom question and click **Ask agents**.
   It must not trigger automatically while typing or on mount.
4. Click **Run live research** only when live research is intentionally enabled.
   It must remain manual and should never trigger the assistant or Groq.
5. If live features are disabled, confirm the UI shows unavailable/disabled
   states rather than stack traces.

## Rollback notes

- Backend rollback: redeploy the previous Git commit in Render.
- Frontend rollback: promote or redeploy the previous Vercel deployment.
- If a demo access code blocks a planned demo, either provide the code to the
  reviewer or temporarily unset `DEMO_ACCESS_CODE` and redeploy the backend.
- If rate limits are too strict during a live walkthrough, lower risk by
  increasing only the request/minute values; do not disable all other safety
  controls unless needed for an emergency demo recovery.

## Cost and rate-limit notes

- The global limiter is in-memory only and resets whenever Render restarts or
  spins down. This is intentional for a portfolio demo and is not suitable for a
  production SaaS.
- Live research and assistant services also keep in-process counters; those
  reset on restart as documented in their env settings.
- Keep live feature daily limits low. Manual single-lead triggers protect cost
  better than automatic background calls.
- Do not add keepalive pings to avoid Render Free sleep; document cold starts
  and use retrying smoke checks instead.

