#!/usr/bin/env bash
# Verifies that a running Sentinel AI stack is healthy. Safe to re-run; changes nothing.
# Works in WSL2, Linux and CI. Usage: infrastructure/scripts/verify-stack.sh
set -u

BACKEND="${BACKEND_URL:-http://localhost:8000}"
WORKER="${WORKER_URL:-http://localhost:8081}"
DEMO="${DEMO_URL:-http://localhost:8080}"
FRONTEND="${FRONTEND_URL:-http://localhost:5173}"

pass=0; fail=0
check() { # name expected_http_code url [grep_pattern]
  local name="$1" want="$2" url="$3" pattern="${4:-}" body code
  body="$(curl -s -m 15 -w '\n%{http_code}' "$url" 2>/dev/null)"
  code="${body##*$'\n'}"; body="${body%$'\n'*}"
  if [[ "$code" != "$want" ]]; then
    printf 'FAIL  %-34s expected HTTP %s, got %s\n' "$name" "$want" "${code:-none}"; fail=$((fail+1)); return
  fi
  if [[ -n "$pattern" ]] && ! grep -qE "$pattern" <<<"$body"; then
    printf 'FAIL  %-34s HTTP %s but body missing /%s/\n' "$name" "$code" "$pattern"; fail=$((fail+1)); return
  fi
  printf 'PASS  %-34s HTTP %s\n' "$name" "$code"; pass=$((pass+1))
}

check "backend liveness"             200 "$BACKEND/api/health"        '"status":"ok"'
check "backend readiness"            200 "$BACKEND/api/health/ready"  '"status":"ready"'
check "  readiness: database ok"     200 "$BACKEND/api/health/ready"  '"name":"database","status":"ok"'
check "  readiness: redis ok"        200 "$BACKEND/api/health/ready"  '"name":"redis","status":"ok"'
check "  readiness: worker ok"       200 "$BACKEND/api/health/ready"  '"name":"browser_worker","status":"ok"'
check "backend OpenAPI docs"         200 "$BACKEND/api/docs"
check "browser-worker liveness"      200 "$WORKER/health"             '"status":"ok"'
check "browser-worker Chromium"      200 "$WORKER/health/ready"       '"status":"ready"'
check "demo-site home"               200 "$DEMO/"                     'Demo Shop'
check "demo-site health"             200 "$DEMO/healthz"
check "demo-site unknown page"       404 "$DEMO/definitely-missing.html"
check "frontend serves the app"      200 "$FRONTEND/"                 '<div id="root">'
check "frontend proxies /api"        200 "$FRONTEND/api/health"       '"status":"ok"'

rid="verify-$(date +%s)-req"
echo "X-Request-ID echo:"
if curl -s -m 10 -D - -o /dev/null -H "X-Request-ID: $rid" "$BACKEND/api/health" | tr -d '\r' | grep -qi "^x-request-id: $rid$"; then
  echo "PASS  backend echoes request id"; pass=$((pass+1))
else
  echo "FAIL  backend did not echo request id"; fail=$((fail+1))
fi

echo; echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
