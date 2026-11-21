# Sentinel AI: Six-Week Implementation Plan

Goal: a reliable, demonstrable MVP in six weeks. Order of work: **deterministic execution before the agent**, and **the demo site early**, so every later feature is verified against a known target with known defects.

## 1. Milestones

### Week 1: Foundation
Monorepo, Docker Compose (frontend, backend, postgres, redis, browser-worker skeleton, demo-site skeleton), FastAPI app, React shell, PostgreSQL + Redis connectivity, migration `0001`, `/api/health` and `/api/health/ready`, structured logging with request IDs, validated configuration, CI, backend/frontend/worker tests, Windows setup docs.

### Week 2: Discovery and security core
URL validation and SSRF module (all four layers), worker session/context lifecycle with request interception, bounded discovery (page/depth/time limits, duplicate and loop prevention), element inventory with safety classification, `discovered_pages` migration, minimal auth (register/login, JWT, ownership checks), project/session creation APIs, **demo site with all seven seeded defects and a ground-truth file**, worker shared-secret check, Chromium seccomp/sandbox verification under Docker.
*Cut line:* if auth slips, ship a single static API token for the MVP and record it as a known gap.

### Week 3: Gemini and test generation
`LLMProvider`, `GeminiProvider`, `MockProvider`, typed errors and retry policy, prompt templates, structured generation (positive, negative, boundary, plus functional/navigation where the inventory supports it), Pydantic schema, grounding check (refs exist), action-allowlist check, deduplication, `test_cases` and `agent_logs` migration, AI-Assisted review UI (list, edit, approve, reject).

### Week 4: Browser execution
`/actions` endpoint with the full typed action set and assertions, evaluation of pass/fail, screenshots, Playwright traces, console/page-error/network capture, `ArtifactStore`, `test_executions` and `evidence` migration, retry policy (retry only on `error`, original failure preserved, flaky flag), manual "run this test" API.

### Week 5: Agent and bug detection
Celery worker, LangGraph workflow with every bound, both modes sharing one pipeline, approvals and cancellation, deterministic bug rules (confirmed vs suspected), evidence-backed bug records, optional LLM triage and suggested-fix text (labelled as LLM output), JSON report, `bugs` and `approval_requests` migration.

### Week 6: Product completion
Dashboard, session creation UI, live monitor (SSE), test-case and bug pages, report page, JSON export, end-to-end test against the demo site, production-style Compose file, documentation pass, demo script and rehearsal.
*Stretch (only if Weeks 1–5 are green):* a small evaluation script that runs the system on the demo site and computes precision/recall against the ground-truth file.

## 2. MVP acceptance criteria

All must be demonstrated by running them, not by reading code.

1. A user can register, log in, and create a project and a testing session for a URL.
2. A private/localhost/metadata URL is rejected, except the explicitly allowed demo host.
3. Discovery finds the demo site's pages within the configured limits and builds an element inventory.
4. Gemini (with a real key) generates structured test cases; invalid output is rejected and retried within limits; the MockProvider path works with no key and is visibly labelled.
5. In AI-Assisted mode, the user reviews and approves cases before any execution.
6. In Autonomous mode, safe cases run automatically; cases needing approval are skipped or paused; blocked cases never run.
7. Playwright executes the approved cases; each attempt records pass/fail, duration, console errors, network failures and screenshots; retries are visible.
8. The seeded defects the MVP covers are detected and recorded as confirmed or suspected bugs with evidence (see §4).
9. Cancelling a running session stops it promptly and cleanly.
10. The user can view a session summary and a detailed report, and export JSON.
11. Backend, frontend and worker tests pass in CI. `docker compose up` starts the stack on a clean machine.
12. No API key reaches the frontend; secrets are absent from the repository.

## 3. Demo site: seeded defects and MVP detection coverage

| # | Seeded defect | Detection route | In MVP? |
|---|---|---|---|
| 1 | Broken internal link (404) | Navigation test, HTTP 404 on internal link | Yes |
| 2 | Incorrect form validation (accepts invalid email) | Negative test assertion fails | Yes |
| 3 | Missing image | `assert_images_loaded`, failed image request | Yes |
| 4 | JavaScript console error | `assert_no_page_errors`, captured `pageerror` | Yes |
| 5 | Incorrect button behaviour (button does nothing) | Functional assertion fails | Yes |
| 6 | Visual layout difference | Needs baseline comparison (OpenCV/SSIM) | **Deferred**, see §5 |
| 7 | Incorrect navigation (link goes to wrong page) | `assert_url` fails after click | Yes |

Six of seven are covered by the MVP. The seventh depends on the deferred visual-regression engine.

## 4. Weekly Definition of Done (summary)

A week is done only when its checklist has been **executed** and results recorded in `DEVELOPMENT_STATUS.md`. Unverified items are listed as unverified. The Week 1 checklist is in §6.

## 5. Deferred post-MVP features

Not silently dropped; these were in the original specification and are consciously deferred to protect the six-week delivery.

| Feature | Why deferred | Prerequisite already in MVP |
|---|---|---|
| Visual regression (OpenCV, SSIM, baselines, approve-baseline UI) | Needs baseline management and a diff UI; independent of execution correctness | Screenshots as evidence |
| Historical bug RAG (Qdrant, embeddings, similar-bug retrieval) | Valuable only after bugs accumulate | `bugs` table, Qdrant Compose profile |
| Full AI evaluation engine and dashboards | MVP ships a stretch precision/recall script only | Ground-truth file, structured bugs |
| PDF export | JSON and dashboard report cover MVP | Report data model (can render via worker `page.pdf` later) |
| Firefox and WebKit | Chromium only for MVP | Browser selection kept as a config field |
| scikit-learn models (duplicate clustering, severity classifier) | Rules are sufficient and more honest at MVP data volume | n/a |
| S3/MinIO storage | Local volume suffices | `ArtifactStore` interface |
| Langfuse tracing | Structured logs and token counts suffice | Provider records usage |
| Egress proxy / firewalling for the worker | Needs infrastructure beyond Compose | Layered SSRF controls |
| Artifact retention/purge setting | Manual purge documented | Predictable artifact paths |

## 5b. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Six weeks is tight | High | Fixed weekly scope, explicit cut lines, stretch items clearly separated |
| Chromium sandbox under Docker Desktop/WSL2 | High | Early check in Week 2; seccomp profile; configurable sandbox flag |
| LLM returns invalid or ungrounded tests | High | Schema + grounding + allowlist; retry cap; mock path for tests |
| False-positive bugs | High | Context-aware rules; `suspected` vs `confirmed`; 4xx not auto-bugged |
| Gemini rate limits or quota during demo | Medium | Backoff, token budget, cached sample generation for the demo, mock fallback clearly labelled |
| Two-language boundary drift | Medium | Zod and Pydantic schemas with contract tests |
| Flaky tests | Medium | Attempts recorded; retry only on `error`; flaky flag |
| Prompt injection | High | Structural defences (refs, allowlist, policy gate) rather than prompt wording |
| Compose not verifiable in the authoring sandbox | Medium | Run the documented verification on the Windows machine and record results |

## 6. Week 1 checklist (Definition of Done)

Status is tracked in `DEVELOPMENT_STATUS.md`. "Verified" there means actually executed.

- [ ] Docker Compose starts the foundation services (frontend, backend, postgres, redis, browser-worker, demo-site)
- [ ] Frontend starts
- [ ] FastAPI starts
- [ ] PostgreSQL connection works
- [ ] Redis connection works
- [ ] Browser-worker health check responds
- [ ] Demo site reachable through the approved setup
- [ ] Migration upgrade works
- [ ] Migration downgrade tested
- [ ] `/api/health` and `/api/health/ready` work (including a failure case)
- [ ] Environment configuration validated (fails fast, clear messages)
- [ ] Structured logs include request IDs
- [ ] At least one backend test and one frontend test pass
- [ ] CI configuration present
- [ ] Windows setup instructions documented
- [ ] `DEVELOPMENT_STATUS.md` accurate
