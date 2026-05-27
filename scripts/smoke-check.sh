#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${BACKEND_URL:-}" ]]; then
  echo "BACKEND_URL is required, for example: BACKEND_URL=https://your-service.onrender.com $0" >&2
  exit 2
fi

base_url="${BACKEND_URL%/}"
health_url="$base_url/health"
status_url="$base_url/api/system/status"

# NOTE: Render Free cold start may take 40-60s.
# Smoke check includes retry logic to avoid false failures.
for attempt in 1 2 3 4 5 6; do
  echo "Checking $health_url (attempt $attempt/6)"
  if curl -fsS --max-time 30 "$health_url" >/dev/null; then
    echo "Health check passed."
    break
  fi
  if [[ "$attempt" == "6" ]]; then
    echo "Health check failed after retries." >&2
    exit 1
  fi
  sleep 15
done

echo "Checking safe system status."
curl -fsS --max-time 30 "$status_url" >/dev/null

if [[ -n "${FRONTEND_ORIGIN:-}" ]]; then
  echo "Checking CORS preflight from $FRONTEND_ORIGIN."
  curl -fsS --max-time 30 \
    -X OPTIONS "$base_url/api/intake/preview" \
    -H "Origin: $FRONTEND_ORIGIN" \
    -H "Access-Control-Request-Method: POST" \
    >/dev/null
fi

echo "Backend smoke checks passed."

