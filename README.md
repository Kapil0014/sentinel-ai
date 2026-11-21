# Sentinel AI

Autonomous AI software testing and bug detection. Enter a URL; Sentinel AI explores the site, asks an LLM (Google Gemini) to propose test cases grounded in what it found, runs the approved cases in a real browser with deterministic Playwright code, and reports bugs with evidence.

> **The LLM proposes; deterministic code decides.** Gemini never emits selectors, JavaScript, or shell commands, and it never decides pass/fail.

**Status: Week 1 of 6 (foundation).** The stack boots, connects to its data stores and reports health. Discovery, test generation, execution and the agent are not built yet. See [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for exactly what has and has not been verified.

## Documentation

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Components, diagrams, API and worker contracts, Gemini design, agent workflow |
| [docs/database.md](docs/database.md) | ERD, tables, migration plan |
| [docs/security.md](docs/security.md) | Threat model, SSRF layers, prompt-injection defences, known gaps |
| [docs/technology_decisions.md](docs/technology_decisions.md) | Why each technology was chosen |
| [docs/implementation_plan.md](docs/implementation_plan.md) | Six-week plan, MVP acceptance criteria, deferred features |

## Services

| Service | Tech | Host URL (localhost only) |
|---|---|---|
| frontend | React + TypeScript + Vite + Tailwind | <http://localhost:5173> |
| backend | FastAPI, SQLAlchemy 2, Alembic | <http://localhost:8000/api/docs> |
| browser-worker | Fastify + Playwright 1.63 (Chromium) | <http://localhost:8081/health> |
| demo-site | nginx static site (test target) | <http://localhost:8080> |
| postgres / redis | PostgreSQL 16 / Redis 7 | `localhost:5432` / `localhost:6379` |

---

## Run it on Windows 11 (Docker Desktop + WSL2)

### One-time setup

1. **Docker Desktop** with the WSL2 backend: *Settings → General → "Use the WSL 2 based engine"*, and *Settings → Resources → WSL integration →* enable your Ubuntu distro.
2. **Keep the repository inside WSL, not on `C:\`.** Bind mounts from Windows drives are slow and break file watching. Open an Ubuntu (WSL) terminal and work in your Linux home directory (`~`), not under `/mnt/c`.

### Start the stack

In the **Ubuntu (WSL)** terminal:

```bash
cd ~
# put the project here, e.g. unzip it or `git clone <your-repo-url> sentinel-ai`
cd sentinel-ai

cp .env.example .env
# Generate a secret and put it in .env as JWT_SECRET=...
python3 -c "import secrets; print(secrets.token_hex(32))"
nano .env          # edit JWT_SECRET; keep LLM_PROVIDER=mock for now

docker compose up --build --wait
```

`--wait` returns only when every service's healthcheck passes. The first build downloads images (the Playwright image is large), so allow several minutes.

### Verify it works

```bash
infrastructure/scripts/verify-stack.sh
```

Expected: `Result: 14 passed, 0 failed`. Then open <http://localhost:5173>; the Dashboard's **System status** panel should show PostgreSQL, Redis and Browser worker as *Operational*.

PowerShell alternative (Windows side, no WSL needed once the stack is up):

```powershell
Invoke-RestMethod http://localhost:8000/api/health/ready | ConvertTo-Json -Depth 5
Invoke-RestMethod http://localhost:8081/health/ready      | ConvertTo-Json -Depth 5
(Invoke-WebRequest http://localhost:8080/).StatusCode
```

### Stop / reset

```bash
docker compose down        # stop, keep database data
docker compose down -v     # stop and DELETE database data and artifacts
```

### Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `set POSTGRES_USER in .env` error | You did not create `.env`. Run `cp .env.example .env` |
| Backend exits with `Invalid configuration:` | Read the listed variables; the message says what is wrong (for example a short `JWT_SECRET`) |
| `browser-worker` unhealthy, `/health/ready` is 503 | Chromium cannot launch. Read `docker compose logs browser-worker`; try `CHROMIUM_SANDBOX=false` in `.env` (development only) |
| Port already in use | Another program uses 5432/6379/8000/8080/8081/5173. Stop it or change the left side of the port mapping in `docker-compose.yml` |
| `\r` / `bad interpreter` errors in scripts | Windows line endings. `.gitattributes` forces LF; re-clone inside WSL, or run `dos2unix` on the file |
| Frontend does not reload on edits | Repo is on a Windows drive. Move it into WSL, or set `CHOKIDAR_USEPOLLING=true` in `.env` |

---

## Run the tests

Everything below runs inside WSL/Linux, outside Docker, against services you start yourself (the quickest way is `docker compose up -d postgres redis`).

**Backend** (Python 3.12):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://sentinel:<your-db-password>@localhost:5432/sentinel
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=<any-string-of-32-or-more-characters>
pytest -q            # unit + integration (integration tests skip if PostgreSQL/Redis are unreachable)
ruff check . && ruff format --check .
```

Integration tests create and drop their own scratch databases, so they never touch your data. Set `REQUIRE_INTEGRATION=1` to make an unreachable service a failure instead of a skip (CI does this).

**Frontend** (Node 22):

```bash
cd frontend && npm ci && npm run lint && npm run typecheck && npm test && npm run build
```

**Browser worker** (Node 22):

```bash
cd browser-worker && npm ci && npm run lint && npm run typecheck && npm test
# Includes a real Chromium launch (needs `npx playwright install --with-deps chromium` first):
RUN_BROWSER_TESTS=1 CHROMIUM_SANDBOX=false npm test
```

**Compose static checks** (no Docker needed): `python infrastructure/scripts/check_compose.py`

## Database migrations

```bash
cd backend
alembic upgrade head       # apply
alembic downgrade base     # roll everything back
alembic current            # show current revision
```

In the development Compose stack, migrations run automatically when the backend starts.

## Configuration and secrets

All configuration is environment variables; see [.env.example](.env.example) (placeholders only). `.env` is git-ignored. The Gemini API key (`GEMINI_API_KEY`) is read only by the backend and is never sent to the browser. With `LLM_PROVIDER=mock` no key is needed, and all mock output is labelled as mock.

## Safety

Sentinel AI drives a browser at websites you point it at. Only test sites you own or are authorised to test. Private/loopback addresses are blocked by default (the bundled demo site is the only exception). It never submits real payments, bypasses CAPTCHAs or authentication, or performs destructive actions. See [docs/security.md](docs/security.md).
