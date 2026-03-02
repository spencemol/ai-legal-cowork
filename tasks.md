# Legal AI Tool — Task Breakdown

> Each task is atomic (5–10 min for a capable agent), mapped to one repo component, and traceable to a requirement from `spec.md`. Integration surfaces are split: one task per side.

**Components:** `infra/` · `api/` · `agents/` · `desktop/` · `shared/`

---

## Phase 0 — Scaffolding & Local Dev Environment

_Goal: Every component boots, lints, type-checks, and has a passing trivial test. Docker infrastructure runs locally._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 0.1 | Create monorepo root with top-level `package.json` (workspaces), root `.gitignore`, and `CLAUDE.md` | root | `ls` shows expected dirs; `.gitignore` covers node_modules, __pycache__, target/, .env | — |
| 0.2 | Add `docker-compose.yml` with Postgres 16 and MongoDB 7 services, health-checks, named volumes | `infra/` | `docker compose up -d` → both containers healthy; `psql` and `mongosh` connect | — |
| 0.3 | Scaffold Node/TypeScript Fastify project: `package.json`, `tsconfig.json` (strict), `src/server.ts` hello-world route, ESLint + Prettier configs | `api/` | `npm run build` succeeds; `npm run lint` passes; `npm run dev` → GET `/health` returns 200 | NFR-4.1 |
| 0.4 | Add Prisma to API with initial empty schema pointing to Postgres from docker-compose | `api/` | `npx prisma generate` succeeds; `npx prisma migrate dev --name init` creates migration | — |
| 0.5 | Scaffold Python project: `pyproject.toml` (with dev deps), `app/main.py` FastAPI hello-world, ruff config | `agents/` | `uv sync` installs; `ruff check .` passes; `uvicorn app.main:app` → GET `/health` returns 200 | — |
| 0.6 | Add Dockerfile for API (multi-stage build, Node 20 slim) | `api/` | `docker build -t legal-api .` succeeds; container starts and `/health` returns 200 | — |
| 0.7 | Add Dockerfile for agents backend (Python 3.12 slim) | `agents/` | `docker build -t legal-agents .` succeeds; container starts and `/health` returns 200 | — |
| 0.8 | Scaffold Tauri 2 + React + TypeScript desktop app with Vite | `desktop/` | `cargo tauri dev` opens window; React renders "Hello World" | — |
| 0.9 | Add `shared/schemas/` with a placeholder JSON schema and `shared/constants/` with roles enum | `shared/` | Files exist and are valid JSON / valid TS | — |
| 0.10 | Add Vitest config to API with a trivial passing test | `api/` | `npm test` → 1 test passes | — |
| 0.11 | Add pytest config to agents with a trivial passing test | `agents/` | `pytest` → 1 test passes | — |
| 0.12 | Add Vitest + React Testing Library config to desktop with a trivial component test | `desktop/` | `npm test` → 1 test passes | — |

---

## Phase 1 — Auth, RBAC & Structured Data CRUD (Node REST API)

_Goal: API authenticates users, enforces roles, and serves CRUD for all core entities. This is the foundation every other component depends on._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 1.1 | Define Prisma schema for `users` table (id, email, name, role enum, password_hash, sso fields, timestamps) | `api/` | `npx prisma migrate dev` succeeds; table exists in Postgres with correct columns | FR-7.1 |
| 1.2 | Implement `POST /auth/register` — hash password (bcrypt), create user, return user object (no hash) | `api/` | `curl` creates user; password_hash stored; plaintext password not returned | FR-7.1 |
| 1.3 | Implement `POST /auth/login` — verify credentials, return signed JWT (access + refresh) | `api/` | Valid creds → 200 + JWT; invalid → 401; JWT payload contains user id, email, role | FR-7.1 |
| 1.4 | Implement JWT validation middleware — verify token, attach user to request context | `api/` | Protected route without token → 401; with valid token → 200 + user in context | FR-7.1, NFR-2.1 |
| 1.5 | Implement RBAC middleware — accept allowed roles, reject unauthorized | `api/` | Partner-only route with paralegal token → 403; with partner token → 200 | FR-7.3 |
| 1.6 | Write unit tests for auth: register, login, JWT validation, RBAC | `api/` | `npm test` → all auth tests pass | FR-7.1, FR-7.3 |
| 1.7 | Define Prisma schema for `matters`, `clients`, `matter_clients`, `matter_assignments` | `api/` | Migration succeeds; all tables and FKs exist | FR-10.1 |
| 1.8 | Implement CRUD routes for `matters` (create, read, list, update) with auth + RBAC | `api/` | Authenticated requests create/read/list/update matters; unauthenticated → 401 | FR-10.1 |
| 1.9 | Implement CRUD routes for `clients` and `matter_clients` (link/unlink) with auth | `api/` | Create client, link to matter, list clients for matter | FR-10.1 |
| 1.10 | Implement `matter_assignments` routes — assign user to matter with access level | `api/` | Assign user to matter → record created; list assignments per matter works | FR-7.2, FR-7.4 |
| 1.11 | Implement matter-scoped access middleware — user can only access matters they are assigned to | `api/` | User assigned to matter A but not B → GET matter B → 403 | FR-7.2, AC-6 |
| 1.12 | Write unit tests for matter-scoped access control | `api/` | Tests cover: assigned user → 200, unassigned → 403, different access levels | FR-7.2, AC-6 |
| 1.13 | Define Prisma schema for `documents` (registry metadata, status enum) | `api/` | Migration succeeds; `documents` table with FK to matters | FR-10.1 |
| 1.14 | Implement CRUD routes for `documents` — register, list by matter, update status | `api/` | Register doc metadata, list docs for a matter, update status to 'indexed' | FR-10.1 |
| 1.15 | Define Prisma schema for `conversations` and `messages` (with citations JSONB) | `api/` | Migration succeeds; both tables exist with correct columns | FR-1.4 |
| 1.16 | Implement CRUD routes for `conversations` — create, list by matter, get with messages | `api/` | Create conversation, add messages, list conversations for matter, get full thread | FR-1.4, AC-8 |
| 1.17 | Define Prisma schema for `audit_logs` | `api/` | Migration succeeds; table exists with user FK, action, metadata JSONB | FR-8.3 |
| 1.18 | Implement audit log service — `logEvent(userId, action, resourceType, resourceId, metadata)` | `api/` | Call service → row in audit_logs; metadata JSONB stored correctly | FR-8.3, NFR-2.3 |
| 1.19 | Add Zod request validation schemas for all routes | `api/` | Invalid payloads → 400 with structured error; valid payloads pass through | NFR-4.1 |
| 1.20 | Implement global error handler middleware (Fastify onError hook) | `api/` | Unhandled throw → 500 JSON response (not stack trace); Zod errors → 400 | NFR-4.1 |

---

## Phase 2 — MCP Server Layer (Node REST API)

_Goal: Expose structured data through MCP so the Python agent backend can call it as tools._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 2.1 | Install `@modelcontextprotocol/sdk`; scaffold MCP server entrypoint in `api/src/mcp/` | `api/` | MCP server starts and lists zero tools | FR-10.2 |
| 2.2 | Register MCP tools for matter queries: `get_matter`, `list_matters`, `get_matter_assignments` | `api/` | MCP `tools/list` returns 3 tools; calling `get_matter` with valid ID returns matter JSON | FR-10.2 |
| 2.3 | Register MCP tools for client queries: `get_client`, `list_clients_for_matter` | `api/` | MCP `tools/list` includes client tools; calling them returns correct data | FR-10.2 |
| 2.4 | Register MCP tools for document registry: `list_documents_for_matter`, `get_document` | `api/` | Tools return document metadata for a given matter | FR-10.2 |
| 2.5 | Register MCP tools for conversations: `get_conversation`, `save_message` | `api/` | Can retrieve conversation thread and persist new messages via MCP | FR-10.2, FR-1.4 |
| 2.6 | Add MCP tool for audit logging: `log_audit_event` | `api/` | Calling tool creates audit_log row | FR-8.3, FR-10.2 |
| 2.7 | Write integration tests for MCP tools (mock Prisma, verify tool responses) | `api/` | `npm test` → MCP tool tests pass | FR-10.2 |

---

## Phase 3 — Ingestion Pipeline (Agents Backend)

_Goal: Parse, chunk, embed, and index documents into Pinecone. Dedup via SHA-256._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 3.1 | Implement SHA-256 file hasher utility | `agents/` | Given a file, returns hex digest; same file → same hash; different file → different hash | FR-5.5 |
| 3.2 | Implement LlamaParse document parser — accept file path, return extracted text + page metadata | `agents/` | Given a sample PDF, returns structured text with page numbers | FR-5.4 |
| 3.3 | Implement semantic chunking — split parsed text into chunks with configurable size/overlap | `agents/` | 10-page doc → N chunks; each chunk ≤ max_tokens; overlap exists between adjacent chunks | FR-5.4 |
| 3.4 | Implement embedding module — `all-MiniLM-L6-v2` via sentence-transformers, batch embed chunks | `agents/` | Given list of strings, returns list of 384-dim float arrays | FR-5.6 |
| 3.5 | Implement Pinecone upsert module — upsert vectors with metadata (document_id, matter_id, chunk_index, access_level, etc.) | `agents/` | After upsert, Pinecone `describe_index_stats` shows increased vector count | FR-5.6 |
| 3.6 | Implement dedup check — query document hash against API, skip if unchanged | `agents/` | Unchanged file → skip; modified file → re-embed; new file → embed | FR-5.5, AC-4 |
| 3.7 | Implement document status tracker — update status via REST API (pending → processing → indexed / failed) | `agents/` | After ingestion, document status in Postgres is 'indexed'; on failure → 'failed' | FR-5.1 |
| 3.8 | Wire end-to-end ingestion: file → hash check → parse → chunk → embed → upsert → status update | `agents/` | Given a new PDF + matter_id, document appears in Pinecone and status = 'indexed' in Postgres | FR-5.1, AC-4 |
| 3.9 | Implement manual refresh endpoint `POST /ingest` — accept file paths + matter_id | `agents/` | POST with file paths → documents ingested; response confirms count | FR-5.2 |
| 3.10 | Write unit tests for hasher, chunker, embedder | `agents/` | `pytest` → ingestion unit tests pass | FR-5.4, FR-5.5 |
| 3.11 | Write integration test for end-to-end ingestion (mock Pinecone + REST API) | `agents/` | `pytest` → ingestion integration test passes | AC-4 |

---

## Phase 4 — Agent Backend Core (Minimal Chat Path)

_Goal: A user query flows through the orchestrator to the retrieval agent, gets a cited answer back via SSE. This is the minimal AI path._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 4.1 | Implement LLM Gateway module — Claude API wrapper with configurable model, temperature, max_tokens | `agents/` | Call gateway with prompt → receive Claude response; model param respected | FR-11.1, NFR-4.2 |
| 4.2 | Implement input sanitizer in gateway — detect/flag common prompt injection patterns | `agents/` | Known injection patterns flagged; clean input passes through | FR-11.2 |
| 4.3 | Implement Presidio PII redactor — detect and replace PII with placeholders ([PERSON_1], [SSN_1]) | `agents/` | Text with names/SSNs → placeholders; mapping table maintained in memory | FR-8.1, AC-5 |
| 4.4 | Implement PII re-hydrator — given access level, selectively restore or keep redactions | `agents/` | Full access → all PII restored; restricted → partial; read_only → all redacted | FR-8.2, AC-5 |
| 4.5 | Implement Pinecone retriever — query by embedding + metadata filter (matter_id, access_level) | `agents/` | Query returns top-K chunks; chunks respect matter_id filter | FR-2.1, FR-7.2 |
| 4.6 | Implement bge-reranker module — rerank retrieved chunks by relevance to query | `agents/` | Given query + 20 chunks, returns reranked top-K with scores | FR-2.4 |
| 4.7 | Implement citation formatter — convert ranked chunks into citation objects (doc_id, chunk_id, snippet, page) | `agents/` | Given reranked chunks, returns citation JSON matching `messages.citations` schema | FR-1.3, FR-2.5 |
| 4.8 | Implement MCP client module — call Node REST API tools from Python (HTTP transport) | `agents/` | Call `get_matter` tool via MCP client → returns matter JSON from Node API | FR-10.2 |
| 4.9 | Implement LangGraph retrieval agent — search → rerank → format citations → return | `agents/` | Given query + matter_id, agent returns answer text + citations array | FR-9.2, AC-1 |
| 4.10 | Implement LangGraph orchestrator agent — classify intent, route to retrieval agent | `agents/` | Factual question → routes to retrieval; routing decision logged | FR-9.1 |
| 4.11 | Implement FastAPI SSE streaming endpoint `POST /chat` — accept query, stream agent response tokens | `agents/` | `curl` to `/chat` with query → SSE events stream back with tokens + final citations | FR-1.2, NFR-1.2 |
| 4.12 | Integrate PII redaction into chat flow — redact before LLM, re-hydrate based on user access level | `agents/` | LangSmith trace shows redacted text sent to LLM; user response has PII appropriate to access level | FR-8.1, FR-8.2, AC-5 |
| 4.13 | Implement MongoDB checkpointer setup (langgraph-checkpoint-mongodb) | `agents/` | Agent run creates checkpoint in MongoDB; checkpoint retrievable by thread_id | FR-9.5, NFR-3.2 |
| 4.14 | Integrate LangSmith tracing — all agent runs and LLM calls traced | `agents/` | Agent run → trace visible in LangSmith dashboard with full span tree | FR-12.1, NFR-5.1 |
| 4.15 | Implement JWT validation in FastAPI — verify token from request header using shared secret with Node API | `agents/` | Request without token → 401; valid token → user context available in endpoint | FR-7.1 |
| 4.16 | Wire access control into `/chat` — extract user's matter assignments, pass to retriever filter | `agents/` | User with access to matter A asks about matter B → no results; matter A → results | FR-7.2, FR-7.4, AC-6 |
| 4.17 | Write unit tests for LLM gateway, PII redactor, retriever, reranker | `agents/` | `pytest` → all unit tests pass | — |
| 4.18 | Write integration test for full chat flow (mock Claude + Pinecone) | `agents/` | `pytest` → chat integration test passes; response contains citations | AC-1 |

---

## Phase 5 — Desktop App (Minimal Usable Client)

_Goal: User can log in, select a matter, ask a question, see a streamed response with citations, and view referenced documents._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 5.1 | Set up Zustand store with auth slice (token, user, login/logout actions) | `desktop/` | Store initializes; login action sets token; logout clears it | — |
| 5.2 | Implement REST API client service (Axios/fetch wrapper with JWT header injection) | `desktop/` | Calls to `/health` include Authorization header; 401 triggers logout | — |
| 5.3 | Implement login page — email + password form, call `POST /auth/login`, store JWT in Tauri secure store | `desktop/` | Enter valid creds → JWT stored → redirected to main view; invalid → error shown | FR-7.1 |
| 5.4 | Implement auth guard — redirect to login if no valid token; auto-attach token to requests | `desktop/` | Unauthenticated user → login page; authenticated → main view | FR-7.1 |
| 5.5 | Implement matter selector — fetch assigned matters from API, display as dropdown/list | `desktop/` | User sees only their assigned matters; selecting one sets active matter in Zustand | FR-7.2 |
| 5.6 | Implement SSE client service — connect to `POST /chat`, parse SSE events, yield tokens | `desktop/` | Connect to agent backend SSE endpoint; tokens arrive incrementally | FR-1.2 |
| 5.7 | Implement chat message input component — text area with send button | `desktop/` | Type message, click send → message appears in chat; input clears | FR-1.1 |
| 5.8 | Implement chat message display component — render user + assistant messages, stream assistant tokens | `desktop/` | User message appears instantly; assistant response streams token-by-token | FR-1.1, FR-1.2 |
| 5.9 | Implement inline citation rendering — parse citation objects, render as clickable links in assistant messages | `desktop/` | Citations appear as numbered links; hovering shows snippet preview | FR-1.3 |
| 5.10 | Implement conversation list sidebar — fetch conversations for active matter, allow switching | `desktop/` | Past conversations listed; clicking one loads its messages | FR-1.4, AC-8 |
| 5.11 | Implement new conversation action — create conversation via API, switch to it | `desktop/` | Click "New Chat" → empty chat created, linked to active matter | FR-1.4 |
| 5.12 | Implement split-view document viewer — read-only pane that opens when citation clicked | `desktop/` | Click citation → document viewer opens on right; shows document content | FR-6.1, FR-6.2 |
| 5.13 | Implement document viewer navigation — scroll/navigate to referenced chunk/section | `desktop/` | Citation click → viewer scrolls to the relevant section | FR-6.3, AC-1 |
| 5.14 | Implement conversation search — search bar that filters conversations by title/content | `desktop/` | Type search term → matching conversations shown | AC-8 |
| 5.15 | Write component tests for login, chat, citation rendering, matter selector | `desktop/` | `npm test` → component tests pass | — |

---

## Phase 6 — End-to-End Integration (Minimal Vertical Slice)

_Goal: All components wired together. A user can log in on desktop, select a matter, ask a question, and receive a streamed cited answer. This is the first fully working system._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 6.1 | Add agents backend to `docker-compose.yml` with dependency on Postgres, MongoDB | `infra/` | `docker compose up` starts API, agents, Postgres, MongoDB; all healthy | — |
| 6.2 | Configure shared JWT secret between API and agents via environment variables | `infra/` | Both services validate the same JWT; token from API login works on agents `/chat` | FR-7.1 |
| 6.3 | Seed script: create test user, matter, assignment, and ingest a sample PDF | `infra/` | Run script → user, matter, assignment exist in Postgres; vectors exist in Pinecone | — |
| 6.4 | E2E smoke test: desktop login → select matter → ask question → streamed cited response | `desktop/` | Manual or scripted: full flow works; response contains relevant citations | AC-1 |
| 6.5 | E2E test: click citation → document viewer opens at correct section | `desktop/` | Citation click opens viewer; viewer scrolls to referenced chunk | AC-1 |
| 6.6 | E2E test: user without matter assignment → no results from that matter's docs | `infra/` | User A (not assigned to matter B) queries matter B → empty results / 403 | AC-6, AC-9 |
| 6.7 | E2E test: PII redacted in LLM trace, re-hydrated per access level in response | `agents/` | LangSmith trace shows placeholders; full-access user sees PII; read-only does not | AC-5 |
| 6.8 | E2E test: conversation persisted and resumable across sessions | `desktop/` | Close and reopen app → previous conversation loads with full history | AC-8 |
| 6.9 | E2E test: audit log records PII access events | `api/` | After chat with PII, audit_logs table has entries with correct user/action/metadata | AC-5, NFR-2.3 |

---

## Phase 7 — Research & Drafting Agents

_Goal: Research agent synthesizes multi-source findings. Drafting agent generates documents from templates or freeform prompts._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 7.1 | Implement DuckDuckGo search tool — query web, return top-N results with snippets | `agents/` | Given query string, returns list of {title, url, snippet} | FR-2.2 |
| 7.2 | Implement legal DB search tool stub — interface for Westlaw/LexisNexis (returns mock data for v1) | `agents/` | Call tool → returns mock case law results; interface ready for real integration | FR-2.3 |
| 7.3 | Implement LangGraph research agent — multi-step: firm data + web + legal DB → synthesize with citations | `agents/` | Research query → agent calls multiple tools → returns synthesized answer with mixed citations | FR-9.3, FR-4.1, AC-3 |
| 7.4 | Wire orchestrator to route research-intent queries to research agent | `agents/` | "What are recent precedents for X?" → routes to research agent (not retrieval) | FR-9.1 |
| 7.5 | Write integration test for research agent flow | `agents/` | `pytest` → research agent test passes; response has web + firm citations | AC-3 |
| 7.6 | Implement Jinja2 template loader — load templates from `agents/app/docgen/templates/` | `agents/` | Given template name, returns Jinja2 template object; missing template → clear error | FR-3.1 |
| 7.7 | Create sample legal document templates (engagement letter, NDA, motion) | `agents/` | 3 `.j2` template files exist with proper placeholder variables | FR-3.1 |
| 7.8 | Implement template-based renderer — populate template with matter context, render to string | `agents/` | Given template + context dict → rendered document string with all placeholders filled | FR-3.1, AC-2 |
| 7.9 | Implement freeform drafting module — LLM generates document from prompt + retrieved context | `agents/` | Given prompt "Draft an NDA for [matter]" → coherent legal document text grounded in matter data | FR-3.2, AC-2 |
| 7.10 | Implement DOCX export — render document string to `.docx` via python-docx | `agents/` | Given rendered text → valid `.docx` file that opens in Word | FR-3.3 |
| 7.11 | Implement PDF export — render via pandoc or weasyprint | `agents/` | Given rendered text → valid `.pdf` file | FR-3.3 |
| 7.12 | Implement Markdown export — render to `.md` file | `agents/` | Given rendered text → valid Markdown file | FR-3.3 |
| 7.13 | Implement LangGraph drafting agent — choose template or freeform → render → export | `agents/` | Drafting request → agent produces file in requested format | FR-9.4, AC-2 |
| 7.14 | Wire orchestrator to route drafting-intent queries to drafting agent | `agents/` | "Draft an NDA for matter X" → routes to drafting agent | FR-9.1 |
| 7.15 | Write integration test for drafting agent (template + freeform paths) | `agents/` | `pytest` → drafting tests pass; output files valid | AC-2 |

---

## Phase 8 — Desktop App: Research & Drafting UI

_Goal: Desktop app exposes research and document generation features._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 8.1 | Extend chat to display research results — mixed citations (firm docs + web + legal DB) | `desktop/` | Research response shows citations with source type badges (internal, web, legal DB) | FR-4.1, AC-3 |
| 8.2 | Implement document generation request UI — select template or freeform, specify params | `desktop/` | User selects template, fills params → request sent to agent backend | FR-3.1, FR-3.2 |
| 8.3 | Implement document download handler — receive generated file from backend, save to local disk via Tauri | `desktop/` | After generation, user prompted to save; file saved to chosen location | FR-3.3 |
| 8.4 | Implement export format selector — DOCX / PDF / Markdown toggle | `desktop/` | User selects format before generation; backend receives correct format param | FR-3.3 |
| 8.5 | Write component tests for research display and document generation UI | `desktop/` | `npm test` → new component tests pass | — |

---

## Phase 9 — Hardening, Observability & Production Readiness

_Goal: Security review, performance validation, pluggable auth, full audit trail._

| # | Task | Component | Verifiable Outcome | Reqs |
|---|------|-----------|--------------------|------|
| 9.1 | Implement pluggable SSO/SAML/OIDC auth — configurable provider per deployment | `api/` | Env var selects auth strategy; SSO login flow works alongside password fallback | FR-7.1, NFR-4.3, AC-6 |
| 9.2 | Implement SSO login flow in desktop app — detect SSO config, redirect to provider | `desktop/` | If SSO configured, login page shows SSO button; clicking opens provider flow | FR-7.1 |
| 9.3 | Add encryption at rest for Postgres (TDE or application-level) | `infra/` | Postgres data directory or sensitive columns encrypted; verified via config | NFR-2.1 |
| 9.4 | Enforce HTTPS/TLS for all inter-service communication | `infra/` | All HTTP calls between services use TLS; plain HTTP rejected | NFR-2.1 |
| 9.5 | Implement Airflow DAG for scheduled re-indexing | `infra/` | Airflow DAG triggers ingestion pipeline on schedule; new/changed docs re-indexed | FR-5.7 |
| 9.6 | Add custom Presidio recognizers for legal entities (case numbers, bar IDs, court names) | `agents/` | Custom entities detected and redacted; standard PII still handled | FR-8.1 |
| 9.7 | Implement prompt injection detection tests — known attack patterns blocked | `agents/` | Test suite of injection patterns → all flagged/blocked by sanitizer | FR-11.2, NFR-2.4 |
| 9.8 | Performance test: simulate 200 concurrent users hitting `/chat` | `infra/` | P95 response time < threshold; no errors; streaming works under load | NFR-1.1, AC-7 |
| 9.9 | Performance test: retrieval across 100K+ vectors | `agents/` | Search returns results in < threshold; relevance maintained | NFR-1.3, AC-7 |
| 9.10 | Security test: cross-matter data leakage — query matter B data while assigned only to matter A | `agents/` | Zero results from unauthorized matter across all agent types | NFR-2.4, AC-9 |
| 9.11 | Security test: privilege escalation — paralegal attempts partner-only actions | `api/` | All partner-restricted endpoints return 403 for paralegal token | AC-6 |
| 9.12 | Audit log completeness test — verify all PII access, doc views, and searches logged | `api/` | After scripted workflow, audit_logs has entries for every auditable action | NFR-2.3, AC-5 |

---

## Dependency Graph (Phase-Level)

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 4 (core agents)
                │                        │
                └──→ Phase 3 (ingest) ───┘
                                         │
                                    Phase 5 (desktop) ──→ Phase 6 (E2E)
                                         │
                                    Phase 7 (research/draft) ──→ Phase 8 (desktop R&D UI)
                                                                      │
                                                                 Phase 9 (hardening)
```

**Critical path to first working demo:** 0 → 1 → 3 + 2 (parallel) → 4 → 5 → 6
