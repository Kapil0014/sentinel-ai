# Development Status

Last updated: **2026-11-20**, end of the Week 1 session.

**Current phase:** Week 1 (Foundation), implemented. **Not fully verified**: Docker Compose has not been executed yet (see below).

Legend: ✅ verified by running it · ⚠️ implemented but **not** verified · ⬜ not started

## Authoring environment (what "verified" means here)

Everything was built in a Linux sandbox that **does not have Docker**. Services were verified by running them **natively** instead: Python 3.12.3, Node 22.23.4, PostgreSQL 16.15, Redis 7.0.15, nginx 1.24, Playwright 1.63.0 with Chromium 153. Anything involving Docker, Docker Desktop, WSL2 or Windows 11 is therefore unverified, and the first thing to do on your machine is run the stack (see "Next step for you").

## Week 1 Definition of Done

| # | Requirement | Status | Evidence / gap |
|---|---|---|---|
| 1 | Docker Compose starts the foundation services | ⚠️ | `docker-compose.yml` and 3 Dockerfiles written. **Never executed.** Static checker passes (7 services, 2 networks) and was proven to catch injected faults. CI job `compose` will run the real `docker compose up --wait` |
| 2 | Frontend starts | ✅ | Vite dev server served the SPA; production build succeeds (`✓ built`); `npm ci` from the lockfile works in a clean copy |
| 3 | FastAPI starts | ✅ | Ran under uvicorn; liveness/readiness/OpenAPI docs return 200 |
| 4 | PostgreSQL connection works | ✅ | Real PG 16.15: readiness `database: ok`; 11 integration tests (10 need PostgreSQL) |
| 5 | Redis connection works | ✅ | Real Redis 7.0.15: readiness `redis: ok` |
| 6 | Browser-worker health check responds | ✅ | `/health` 200; `/health/ready` launched **real Chromium 153** and returned 200. Ran with `CHROMIUM_SANDBOX=false` (sandbox is root here) |
| 7 | Demo site accessible | ✅ native / ⚠️ Docker | Real `nginx.conf` validated and served by nginx 1.24: all 5 pages and `/healthz` return 200, unknown page 404, security headers present. The Docker image (nginx 1.27) is unbuilt |
| 8 | Migration upgrade works | ✅ | `alembic upgrade head` created the 4 tables + named CHECK constraints; also tested in pytest |
| 9 | Migration downgrade tested | ✅ | `downgrade base` leaves only `alembic_version`; upgrade→downgrade→upgrade round-trip tested; a **schema-drift test** compares models to the migrated schema |
| 10 | Health and readiness endpoints work | ✅ | Including failure paths on a **running server**: stopping PostgreSQL → HTTP 503 within seconds, stopping Redis → 503, liveness stays 200, both recover automatically. Worker down → still `ready` (it is optional) |
| 11 | Environment configuration validated | ✅ | 16 config unit tests cover short `JWT_SECRET`, `LLM_PROVIDER=gemini` without a key, wrong DB driver, wildcard CORS, placeholder secret / private hosts in production. A **real process** was run only for the short-secret case: it exited with code 1 and a one-line readable message (no traceback) |
| 12 | Structured logs include request IDs | ✅ | Backend and worker emit JSON; a caller-supplied `X-Request-ID` appeared in the backend log and the response; malformed IDs are replaced; secrets/URL passwords are redacted (tested, and 0 occurrences of the DB password in the server log) |
| 13 | ≥1 backend and ≥1 frontend test pass | ✅ | Backend **44**, frontend **16**, worker **16** (+1 opt-in real-browser test, passed: 17/17 when enabled) |
| 14 | CI configuration present | ⚠️ | `.github/workflows/ci.yml` is valid YAML and mirrors the commands that passed locally. **Has not run on GitHub** |
| 15 | Windows setup instructions documented | ⚠️ | In README (WSL2 + Docker Desktop + PowerShell alternatives). Written, not executed on Windows 11 |
| 16 | DEVELOPMENT_STATUS.md accurate | ✅ | This file; each ✅ above was observed in this session |

**Week 1 verdict: functionally complete and verified natively; the Docker/Windows layer is the remaining gap, and Week 1 should not be closed until you have run the commands below.**

## Test results (final run on the committed tree)

| Suite | Result |
|---|---|
| Backend pytest (`REQUIRE_INTEGRATION=1`) | 44 passed (33 unit, 11 integration) |
| Backend without DB credentials | 34 passed, 10 skipped (the 10 that need PostgreSQL skip cleanly) |
| Backend ruff check / format | clean |
| Frontend vitest | 16 passed; eslint, `tsc`, production build clean |
| Browser-worker vitest | 16 passed, 1 skipped; **17 passed** with `RUN_BROWSER_TESTS=1` |
| Clean-room reinstall (new venv, `npm ci` ×2 in a fresh copy) | all green |
| `verify-stack.sh` against live native stack | 14 passed, 0 failed; with the worker stopped it failed exactly the 3 worker checks |
| `check_compose.py` | OK; negative test caught 4/4 injected faults |
| Secrets scan (Gemini-key pattern, local DB password) | no matches |

## Implemented (Week 1 scope)

- Monorepo: `backend/`, `frontend/`, `browser-worker/`, `demo-site/`, `infrastructure/`, `docs/`.
- Backend: validated settings, structlog JSON logging with redaction, request-ID middleware, async SQLAlchemy engine, models and migration `0001` for `users`, `projects`, `websites`, `testing_sessions`, `GET /api/health`, `GET /api/health/ready`.
- Browser worker: Fastify service with `/health` and a cached real-Chromium `/health/ready`.
- Frontend: routed shell, live system-status panel, honest "not implemented (planned Week N)" pages; no fake data.
- Demo site: clean static skeleton (5 pages). **No defects seeded yet.**
- Docker Compose (two networks, healthchecks, loopback-only ports, Qdrant behind profile `rag`), CI workflow, `verify-stack.sh`, `check_compose.py`.
- Six Phase 0 documents.

## Not implemented yet (do not assume these work)

Everything beyond health checks: authentication, URL validation / **SSRF protection**, discovery, DOM extraction, Gemini/Mock providers, test generation, execution, agent, bug detection, reports, dashboard data, worker shared-secret check. Deferred post-MVP items are listed in `docs/implementation_plan.md` §5.

## Known issues, risks and decisions to review

1. **Docker never executed.** Unverified assumptions: image tags `mcr.microsoft.com/playwright:v1.63.0-noble`, `nginx:1.27-alpine`, `qdrant/qdrant:v1.12.4` exist; `wget` is available in the alpine images for healthchecks; the bind-mount + `--reload` dev loop works on your setup.
2. **Chromium sandbox is OFF by default in development** (`CHROMIUM_SANDBOX=false`) because the container sandbox/seccomp setup is unverified on Docker Desktop. The worker logs a warning when disabled. Must be solved in Week 2 and must be `true` in production.
3. **No Python lockfile.** `requirements.txt` uses compatible-range pins (the Node side has lockfiles). Consider `pip-compile`/`uv` later.
4. **Default Gemini model name** (`gemini-2.5-flash`) is an unverified placeholder; no Gemini code exists yet. Confirm against current Gemini docs in Week 3.
5. **Dependency versions are very recent** (Vite 8, Vitest 5, ESLint 10, React 19.3, Fastify 5.12). They work here; if you hit tooling friction on your machine, that is the first place to look.
6. **Integration tests need DB privileges** to create scratch databases (fine for the local/CI Postgres user).
7. Readiness treats the browser worker as *optional* by design, so the API reports `ready` while the worker is down. The UI shows it as "Unavailable (optional)".
8. The authoring sandbox recycled my background services between turns once; this affected only my manual checks, not the code.

## Commands to run on your Windows 11 machine

In an **Ubuntu (WSL2)** terminal, with the project inside `~` (not `/mnt/c`):

```bash
cd ~/sentinel-ai
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste into JWT_SECRET= in .env
docker compose up --build --wait
infrastructure/scripts/verify-stack.sh                      # expect: 14 passed, 0 failed
```

Then open <http://localhost:5173> (System status panel) and <http://localhost:8000/api/docs>. Full instructions and troubleshooting are in `README.md`.

## Next step for you

1. Run the commands above. If anything fails, send me the output of `docker compose ps` and `docker compose logs <service>`; I will fix the root cause and update this file.
2. Push to GitHub so the CI `compose` job gives a second, independent verification.

## Next development task: Week 2

URL validation + SSRF module (all four layers, with a test per rule), worker session/context lifecycle with request interception, bounded discovery and element inventory, `discovered_pages` migration, minimal auth, demo site with the 7 seeded defects and `ground-truth.json`, worker shared-secret header, and the Chromium seccomp/sandbox fix. Cut line: if auth slips, use a static API token and record it as a gap.
