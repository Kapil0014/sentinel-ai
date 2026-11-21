# Sentinel AI: Technology Decisions

Short decision records. Each lists the choice, why, the alternative, and the cost we accept. Decisions marked **(approved)** were fixed in the architecture review and are not reopened.

| # | Decision | Status |
|---|---|---|
| 1 | Backend: Python + FastAPI + Pydantic v2 | approved |
| 2 | ORM and migrations: SQLAlchemy 2 + Alembic + PostgreSQL | approved |
| 3 | Single DB driver: `psycopg` v3 | new |
| 4 | Agent orchestration: LangGraph | approved |
| 5 | LLM: Gemini behind a provider interface, plus MockProvider | approved |
| 6 | Browser automation: Playwright in a TypeScript worker, internal HTTP | approved |
| 7 | Worker HTTP framework: Fastify + Zod | new |
| 8 | Background jobs: Celery + Redis, introduced Week 5 | approved, timing refined |
| 9 | Live updates: SSE, fetch-based client | approved, detail added |
| 10 | Frontend: React + TS + Vite + Tailwind v4 + Recharts + Vitest | approved |
| 11 | LLM refers to element refs, never selectors | new |
| 12 | Logging: structlog (JSON) with request IDs | new |
| 13 | Lint/format: Ruff (Python), ESLint (TS) | new |
| 14 | Storage: local filesystem behind an interface | approved |
| 15 | Docker Compose with two networks and profiles | refined |
| 16 | Deferred technologies | documented |

---

**1. FastAPI + Pydantic v2.** Native async, request validation, and automatic OpenAPI docs. The same Pydantic models validate LLM output, which keeps validation in one idiom. *Alternative:* Django (heavier, less natural for async work). *Cost:* we assemble auth and admin ourselves.

**2. SQLAlchemy 2 + Alembic + PostgreSQL.** Relational integrity for sessions → tests → executions → bugs → evidence, JSONB where payloads vary. Typed `Mapped[]` models give editor support. *Alternative:* SQLModel (thinner, less mature migrations story). *Cost:* more boilerplate.

**3. `psycopg` v3 only.** One driver serves sync (Alembic, tests) and async (application engine) through the same `postgresql+psycopg://` URL. The usual alternative, `asyncpg` for the app plus `psycopg2` for Alembic, means two drivers with different behaviour. *Cost:* slightly less raw throughput than asyncpg, irrelevant at our scale.

**4. LangGraph.** Explicit nodes and edges, conditional routing, checkpointing and human-in-the-loop interrupts map directly onto our state machine (architecture §5). *Alternative:* a hand-written loop (simpler but no checkpoint/interrupt). *Cost:* a new framework to learn in Week 5. Mitigation: the state machine is specified now, and the node functions are plain, independently testable Python.

**5. Gemini through `LLMProvider`.** The agent depends on a `Protocol`, not on Google's SDK. We use the `google-genai` SDK inside `GeminiProvider` only. `MockProvider` keeps all automated tests free and deterministic and labels its output `source="mock"`. *Cost:* the lowest-common-denominator interface hides provider-specific features. Acceptable.

**6. Playwright in TypeScript, separate service.** Playwright's accessibility-first locators (`getByRole`, `getByLabel`) are best supported in its native Node implementation. Putting the browser in its own container is also the main security boundary (security.md §3). *Alternative:* Python Playwright inside the backend (one language, but untrusted content then runs next to our database credentials). *Cost:* two languages and an HTTP contract to maintain; mitigated by schemas on both sides and contract tests.

**7. Fastify + Zod in the worker.** Built-in schema validation hooks, fast, and `inject()` allows HTTP-level tests without opening a port. *Alternative:* Express (more familiar, needs extra libraries for validation and test harness).

**8. Celery + Redis, from Week 5.** Mature, well known in interviews, supports retries and time limits. Runs in a Linux container, so the Windows prefork limitation does not apply. Sessions are long and I/O bound, so each task runs one session via `asyncio.run(...)`. Cancellation is a database flag checked between steps, not `revoke(terminate=True)`, which is unsafe for browser work. *Alternative:* ARQ (asyncio-native, simpler, but quieter maintenance). *Not in Week 1:* nothing enqueues jobs yet; adding an idle worker would be untestable ceremony.

**9. SSE with a fetch-based reader.** One-directional streaming is all the monitor needs; commands use REST. Native `EventSource` cannot send an `Authorization` header, so the frontend reads the stream via `fetch`. Events are persisted before publishing so reconnects replay without loss. *Alternative:* WebSockets (bidirectional, more connection state to manage).

**10. Vite + Tailwind v4 + Vitest.** Fast dev server and tests that share Vite's config. Tailwind v4 integrates through its Vite plugin with no PostCSS config. Recharts is added with the dashboard in Week 6 (not installed earlier, to keep Week 1 lean). *Alternative:* Next.js (SSR is unnecessary for an authenticated dashboard).

**11. Element refs instead of selectors.** The worker builds an inventory of interactive elements and gives each an opaque ref. The LLM writes `target_ref: "el_12"`. Code maps refs to locators. A hallucinated or injected selector is therefore not representable. This is the single most important security and reliability decision in the AI layer. *Cost:* the LLM cannot target something the inventory missed; discovery quality bounds test quality, and that limitation is documented.

**12. structlog.** JSON logs with `request_id` bound through `contextvars` for every log line in a request. *Alternative:* stdlib `logging` + a JSON formatter (more manual binding).

**13. Ruff and ESLint.** One fast tool for Python lint and format; the standard TypeScript lint stack. Both run in CI.

**14. Storage interface.** `ArtifactStore` with a `LocalArtifactStore` implementation (root from `ARTIFACTS_DIR`). An S3/MinIO implementation can be added without touching callers. Introduced in Week 4 when the first artifact is written.

**15. Compose layout.** Two networks (`app_net`, `browser_net`), healthchecks on every service, named volumes for Postgres data, artifacts and frontend `node_modules`, host ports bound to `127.0.0.1` for data stores. Qdrant under `profiles: [rag]`. *Windows note:* keep the repository inside the WSL2 filesystem (`~/sentinel-ai`), because bind mounts from `C:\` are slow and break file watchers.

**16. Deferred (post-MVP):** Qdrant and embeddings (RAG), OpenCV/SSIM visual regression, evaluation engine and precision/recall tooling, PDF export, Firefox/WebKit, scikit-learn classifiers, S3/MinIO, Langfuse, egress proxy. See [implementation_plan.md](implementation_plan.md).
