# Legal AI Tool

A desktop application for law firms providing conversational AI, document retrieval (RAG), legal research, and document generation — with strict access control, PII protection, and data residency. Each firm self-hosts an isolated instance.

> Spec-driven development (SDD) dry-run project built with Claude Code agents.

---

## Architecture Overview

```
Tauri Desktop App (React + TypeScript)
  │
  ├── SSE ──► Python Agent Backend (FastAPI + LangGraph)
  │              │
  │              ├── HTTP/REST ──► Node REST API (Fastify)
  │              ├── Local ──► Presidio (PII redaction)
  │              ├── Local ──► sentence-transformers (embeddings)
  │              ├── HTTP ──► Pinecone (vector search)
  │              ├── HTTP ──► Claude API (via LLM Gateway)
  │              ├── HTTP ──► DuckDuckGo (web search)
  │              ├── MongoDB (LangGraph checkpoints)
  │              └── LangSmith (observability)
  │
  └── HTTP/REST ──► Node REST API (Fastify + TypeScript strict)
                      │
                      └── Postgres (users, matters, clients, audit logs)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Desktop | Tauri 2 + React 18 + TypeScript 5 + Zustand |
| REST API | Fastify 5 + TypeScript (strict) + Prisma 5 + Zod 4 ([details](api/README.md)) |
| Agent Backend | FastAPI + Python 3.12 + LangGraph |
| Databases | PostgreSQL 16 · MongoDB 7 · Pinecone |
| Auth | JWT (@fastify/jwt) + bcrypt |
| Testing | Vitest 4 (Node/React) · Pytest 8 (Python) |
| Linting | ESLint + Prettier (TS) · Ruff (Python) |
| Infrastructure | Docker Compose · Apache Airflow (planned) |

---

## Project Structure

```
ai-legal-cowork/
├── api/                         # Node REST API (Fastify + TypeScript) — [README](api/README.md)
│   ├── src/
│   │   ├── server.ts            # Fastify app factory + error handler
│   │   ├── db.ts                # Prisma client singleton
│   │   ├── auth/
│   │   │   └── password.ts      # bcrypt hashing/verification
│   │   ├── middleware/
│   │   │   ├── authenticate.ts  # JWT verification
│   │   │   ├── rbac.ts          # Role-based access control
│   │   │   └── matterAccess.ts  # Matter-level access control
│   │   ├── routes/
│   │   │   ├── auth.ts          # Register, login, me
│   │   │   ├── matters.ts       # Matter CRUD + assignments
│   │   │   ├── clients.ts       # Client CRUD + matter linking
│   │   │   ├── documents.ts     # Document registry + status
│   │   │   └── conversations.ts # Conversations + messages
│   │   ├── mcp/                 # MCP server layer (Phase 2)
│   │   │   ├── server.ts        # createMcpServer() factory (McpServer)
│   │   │   └── tools/
│   │   │       ├── matters.ts       # get_matter, list_matters, get_matter_assignments
│   │   │       ├── clients.ts       # get_client, list_clients_for_matter
│   │   │       ├── documents.ts     # list_documents_for_matter, get_document
│   │   │       ├── conversations.ts # get_conversation, save_message
│   │   │       └── audit.ts         # log_audit_event
│   │   ├── schemas/             # Zod validation schemas
│   │   └── services/
│   │       └── audit.ts         # Audit log service
│   ├── tests/                   # Vitest test suite (10 test files, 113 tests)
│   ├── prisma/
│   │   └── schema.prisma        # 9 models, 6 enums
│   ├── Makefile                 # make test, make lint, make test-watch, etc.
│   └── Dockerfile
├── agents/                      # Python agent backend (FastAPI) — [README](agents/README.md)
│   ├── app/
│   │   ├── main.py              # FastAPI app + route registration
│   │   ├── gateway/             # LLM Gateway (Phase 4)
│   │   │   ├── client.py        # LLMGateway — Claude API wrapper (configurable model/temp/max_tokens)
│   │   │   └── sanitizer.py     # InputSanitizer — prompt injection detection
│   │   ├── pii/                 # PII management (Phase 4)
│   │   │   ├── redactor.py      # PIIRedactor (Presidio) + PIIRehydrator (access-level-aware)
│   │   │   └── audit.py         # PIIAuditLogger
│   │   ├── retrieval/           # RAG retrieval (Phase 4)
│   │   │   ├── retriever.py     # PineconeRetriever — metadata-filtered vector search
│   │   │   ├── reranker.py      # BGEReranker — FlagReranker-backed re-ranking
│   │   │   └── citations.py     # CitationFormatter — chunk → citation JSONB
│   │   ├── mcp_client/          # MCP client (Phase 4)
│   │   │   └── client.py        # MCPClient — HTTP calls to Node API MCP tools
│   │   ├── agents/              # LangGraph agents (Phase 4)
│   │   │   ├── retrieval_agent.py # Retrieval agent: search → rerank → cite
│   │   │   ├── orchestrator.py  # Orchestrator: intent classification → routing
│   │   │   ├── checkpointer.py  # MongoCheckpointerFactory (langgraph-checkpoint-mongodb)
│   │   │   └── tracing.py       # TracingConfig — LangSmith env-var setup
│   │   ├── auth/                # Auth (Phase 4)
│   │   │   └── jwt_validator.py # JWTValidator + require_auth dependency (python-jose HS256)
│   │   ├── rag/                 # Ingestion pipeline (Phase 3)
│   │   │   ├── models.py        # Pydantic models (PageContent, TextChunk, VectorRecord…)
│   │   │   ├── hasher.py        # SHA-256 file hasher
│   │   │   ├── parser.py        # LlamaParse wrapper
│   │   │   ├── chunker.py       # Sentence-boundary chunker + ChunkConfig
│   │   │   ├── embedder.py      # all-MiniLM-L6-v2 embedding wrapper
│   │   │   ├── pinecone_store.py # Pinecone batched upsert
│   │   │   ├── api_client.py    # Node REST API HTTP client
│   │   │   └── ingestion.py     # End-to-end pipeline orchestration
│   │   └── routes/
│   │       ├── ingest.py        # POST /ingest endpoint
│   │       └── chat.py          # POST /chat SSE streaming endpoint (Phase 4)
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── ingestion/           # Phase 3 test suite (68 tests)
│   │   │   ├── conftest.py
│   │   │   ├── test_hasher.py
│   │   │   ├── test_chunker.py
│   │   │   ├── test_embedder.py
│   │   │   ├── test_parser.py
│   │   │   ├── test_pinecone_store.py
│   │   │   ├── test_api_client.py
│   │   │   ├── test_ingestion_integration.py
│   │   │   └── test_ingest_endpoint.py
│   │   └── phase4/              # Phase 4 test suite (145 tests)
│   │       ├── conftest.py
│   │       ├── test_gateway.py          # LLM Gateway + input sanitizer
│   │       ├── test_pii.py              # PII redactor + rehydrator
│   │       ├── test_retriever.py        # Pinecone retriever
│   │       ├── test_reranker.py         # BGE reranker
│   │       ├── test_citations.py        # Citation formatter
│   │       ├── test_mcp_client.py       # MCP HTTP client
│   │       ├── test_retrieval_agent.py  # LangGraph retrieval agent
│   │       ├── test_orchestrator.py     # LangGraph orchestrator
│   │       ├── test_chat_endpoint.py    # SSE /chat endpoint + JWT + access control
│   │       ├── test_checkpointer.py     # MongoDB checkpointer
│   │       ├── test_langsmith.py        # LangSmith tracing config
│   │       └── test_chat_integration.py # Full chat flow integration
│   ├── pyproject.toml
│   └── Dockerfile
├── desktop/                     # Tauri 2 + React desktop app (Phase 5)
│   ├── src/
│   │   ├── types/index.ts       # Shared TS interfaces: User, Matter, Citation, Message, Conversation
│   │   ├── stores/
│   │   │   ├── authStore.ts     # Zustand auth slice (token, user, login/logout)
│   │   │   └── chatStore.ts     # Zustand chat state (active matter, conversations, messages)
│   │   ├── services/
│   │   │   ├── apiClient.ts     # fetch wrapper with JWT header injection + 401 auto-logout
│   │   │   ├── tokenStorage.ts  # Tauri Store (production) / localStorage (tests) abstraction
│   │   │   └── sseClient.ts     # POST SSE client via fetch + ReadableStream
│   │   ├── components/
│   │   │   ├── AuthGuard/       # Route guard: login page vs main view
│   │   │   ├── LoginPage/       # Email + password form → JWT
│   │   │   ├── MatterSelector/  # Dropdown: assigned matters → active matter
│   │   │   ├── Chat/            # ChatInput, ChatMessage, ChatWindow
│   │   │   ├── Citations/       # CitationLink: numbered inline [N] with hover tooltip
│   │   │   ├── ConversationList/ # Sidebar: list, new chat, search
│   │   │   └── DocumentViewer/  # Split-view read-only pane, chunk highlight + scroll
│   │   ├── main.tsx             # React entry
│   │   ├── App.tsx              # AuthGuard → LoginPage / MainView
│   │   └── App.test.tsx         # App render tests
│   ├── src-tauri/               # Rust backend (Tauri 2)
│   │   ├── src/
│   │   └── Cargo.toml
│   └── vite.config.ts
├── shared/                      # Cross-service schemas & constants
│   ├── schemas/
│   │   └── citation.json
│   └── constants/
│       └── roles.ts
├── infra/
│   └── docker-compose.yml       # Postgres 16 + MongoDB 7
├── spec.md                      # Product specification
├── plan.md                      # System design & architecture
├── tasks.md                     # Phase-level task breakdown
└── CLAUDE.md                    # AI agent instructions
```

---

## Data Models (Postgres via Prisma)

| Model | Purpose |
|-------|---------|
| **User** | Attorneys, paralegals, partners (role enum) |
| **Matter** | Legal cases with status tracking |
| **Client** | Parties involved in matters |
| **MatterClient** | Many-to-many: clients ↔ matters |
| **MatterAssignment** | User access to matters (full/restricted/read_only) |
| **Document** | File registry with ingestion status tracking |
| **Conversation** | Chat sessions linked to matters |
| **Message** | Chat messages with JSONB citations |
| **AuditLog** | Action audit trail with JSONB metadata |

---

## API Endpoints

### Node REST API (`http://localhost:3000`)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/register` | Register user |
| `POST` | `/auth/login` | Login → JWT (access + refresh) |
| `GET` | `/auth/me` | Current user context |
| `POST/GET/PUT` | `/matters` | Matter CRUD |
| `POST/GET/DELETE` | `/matters/:id/assignments` | User ↔ matter assignments |
| `POST/GET` | `/clients` | Client CRUD |
| `POST/GET/DELETE` | `/matters/:id/clients` | Client ↔ matter linking |
| `POST/GET` | `/matters/:id/documents` | Document registry |
| `PATCH` | `/documents/:id/status` | Ingestion status updates |
| `POST/GET` | `/matters/:id/conversations` | Conversation management |
| `POST` | `/conversations/:id/messages` | Add messages |
| `GET` | `/health` | Health check |

### Python Agent Backend (`http://localhost:8000`)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/chat` | Streaming SSE chat — JWT required, sends `matter_id` + `query`; streams tokens + `citations` event |
| `POST` | `/ingest` | Trigger document ingestion — accepts `file_paths` + `matter_id` |
| `GET` | `/health` | Health check |

---

## MCP Server Layer

The Node REST API doubles as an **MCP server**, exposing 10 tools so the Python agent backend can query structured data (matters, clients, documents, conversations) and write audit logs from within LangGraph agents — without coupling the agent code to raw REST calls.

| Tool group | Tools |
|------------|-------|
| Matters | `get_matter` · `list_matters` · `get_matter_assignments` |
| Clients | `get_client` · `list_clients_for_matter` |
| Documents | `list_documents_for_matter` · `get_document` |
| Conversations | `get_conversation` · `save_message` |
| Audit | `log_audit_event` |

See [api/README.md — MCP Server Layer](api/README.md#mcp-server-layer-phase-2) for full tool reference, design decisions, and test strategy.

---

## Test Coverage

### API (`api/tests/`) — 10 test files, 113 tests

| Test File | Coverage |
|-----------|----------|
| `auth.test.ts` | Registration, login, JWT validation, RBAC guards |
| `matters.test.ts` | Matter CRUD, updates, access checks |
| `assignments.test.ts` | User-matter assignments, RBAC, access levels |
| `clients.test.ts` | Client CRUD, matter linking/unlinking |
| `documents.test.ts` | Document registration, status updates |
| `conversations.test.ts` | Conversation + message CRUD, citations |
| `audit.test.ts` | Audit event logging, metadata storage |
| `error-handling.test.ts` | Zod validation errors, global error handler |
| `health.test.ts` | Server bootstrap |
| `mcp-tools.test.ts` | All 10 MCP tools via InMemoryTransport (Tasks 2.1–2.7) |

### Agents (`agents/tests/`) — 20 test files (213 tests)

**Phase 3 — Ingestion (8 files, 68 tests)**

| Test File | Coverage |
|-----------|----------|
| `test_health.py` | FastAPI health endpoint |
| `ingestion/test_hasher.py` | SHA-256 hasher: hex digest, determinism, empty file |
| `ingestion/test_chunker.py` | Sentence chunker: max_chars, overlap, page numbers, edge cases |
| `ingestion/test_embedder.py` | Embedder: 384-dim output, batch, injection, lazy model |
| `ingestion/test_parser.py` | LlamaParse wrapper: pages, page numbers, file hash, empty doc |
| `ingestion/test_pinecone_store.py` | Pinecone upsert: IDs, metadata, batching, empty input |
| `ingestion/test_api_client.py` | REST API client: GET docs, register, status PATCH, camelCase payload |
| `ingestion/test_ingestion_integration.py` | End-to-end pipeline: new file, dedup skip, failure → failed status, ingest_many counts |
| `ingestion/test_ingest_endpoint.py` | POST /ingest: 200 schema, 422 validation, empty list |

**Phase 4 — Agent Backend Core (12 files, 145 tests)**

| Test File | Coverage |
|-----------|----------|
| `phase4/test_gateway.py` | LLM Gateway: prompt call, model params; Input sanitizer: injection patterns |
| `phase4/test_pii.py` | PIIRedactor: placeholder format, mapping table; PIIRehydrator: full/restricted/read_only |
| `phase4/test_retriever.py` | PineconeRetriever: matter_id + access_level metadata filter, top-K |
| `phase4/test_reranker.py` | BGEReranker: score pairs, top-K, sorted descending |
| `phase4/test_citations.py` | CitationFormatter: doc_id, chunk_id, text_snippet, page schema |
| `phase4/test_mcp_client.py` | MCPClient: HTTP tool calls, get_matter, list_matters |
| `phase4/test_retrieval_agent.py` | LangGraph retrieval agent: retrieve → rerank → generate → cite |
| `phase4/test_orchestrator.py` | LangGraph orchestrator: intent classification, routing to retrieval |
| `phase4/test_chat_endpoint.py` | POST /chat SSE: JWT auth, matter access, token streaming, citations |
| `phase4/test_checkpointer.py` | MongoCheckpointerFactory: env config, langgraph-checkpoint-mongodb |
| `phase4/test_langsmith.py` | TracingConfig: env vars, from_env(), configure_tracing() |
| `phase4/test_chat_integration.py` | Full chat flow: JWT → orchestrator → retrieval → SSE cited response |

### Desktop (`desktop/src/`) — 13 test files (73 tests)

| Test File | Coverage |
|-----------|----------|
| `stores/authStore.test.ts` | Zustand auth slice: login, logout, isAuthenticated |
| `services/apiClient.test.ts` | JWT header injection, 401 → logout, JSON parsing |
| `services/sseClient.test.ts` | POST SSE: token events, citations event, error handling |
| `components/LoginPage/LoginPage.test.tsx` | Form submit, error display, redirect on success |
| `components/AuthGuard/AuthGuard.test.tsx` | Unauthenticated → login; authenticated → main view |
| `components/MatterSelector/MatterSelector.test.tsx` | Fetch matters, dropdown, set active matter |
| `components/Chat/ChatInput.test.tsx` | Textarea, send button, Enter to send, clears on submit |
| `components/Chat/ChatMessage.test.tsx` | User/assistant rendering, streaming cursor, citation refs |
| `components/Chat/ChatWindow.test.tsx` | Integrated chat: input + messages + SSE |
| `components/Citations/CitationLink.test.tsx` | Numbered links, hover tooltip, onClick |
| `components/ConversationList/ConversationList.test.tsx` | List, new chat, search filter, switching |
| `components/DocumentViewer/DocumentViewer.test.tsx` | Open/close, content, chunk highlight + scroll |
| `App.test.tsx` | Auth-gated routing: login page vs main view |

---

## Implementation Status

### Phase 0: Foundation & Scaffolding — COMPLETE

All scaffolding tasks (0.1–0.12) are done. Monorepo, Docker infrastructure, all three runtimes (Node, Python, Rust/React) boot, lint, type-check, and have passing tests.

### Phase 1: Node REST API + Auth — COMPLETE

All Phase 1 tasks (1.1–1.20) are implemented and tested:

- [x] Prisma schema with all 9 models and migrations
- [x] User registration + bcrypt password hashing
- [x] JWT login with access/refresh tokens
- [x] JWT verification middleware
- [x] RBAC middleware (role-based route guards)
- [x] Matter-level access control middleware (partners get implicit global access)
- [x] Full CRUD: matters, clients, matter_clients, matter_assignments
- [x] Document registry with status tracking
- [x] Conversations + messages with JSONB citations
- [x] Audit log service
- [x] Zod request validation on all routes
- [x] Global error handler (Zod → 400, unhandled → 500)
- [x] Comprehensive test suite (9 test files, Prisma mocked)

### Phase 2: MCP Server Layer — COMPLETE

All Phase 2 tasks (2.1–2.7) are implemented and tested. See [api/README.md](api/README.md) for full details.

- [x] `createMcpServer()` factory (`api/src/mcp/server.ts`) using `McpServer` from `@modelcontextprotocol/sdk` v1.27
- [x] Matter tools: `get_matter`, `list_matters`, `get_matter_assignments`
- [x] Client tools: `get_client`, `list_clients_for_matter`
- [x] Document tools: `list_documents_for_matter`, `get_document`
- [x] Conversation tools: `get_conversation`, `save_message` (with optional citations JSONB)
- [x] Audit tool: `log_audit_event` (with optional metadata and IP address)
- [x] 25 integration tests via `InMemoryTransport` — Prisma mocked, no network required

### Phase 3: Ingestion Pipeline — COMPLETE

All Phase 3 tasks (3.1–3.11) are implemented and tested.  See [agents/README.md](agents/README.md) for full details.

- [x] SHA-256 file hasher (`app/rag/hasher.py`) — deterministic dedup key
- [x] LlamaParse document parser (`app/rag/parser.py`) — PDF → page-structured text, injected client for testability
- [x] Sentence-boundary chunker (`app/rag/chunker.py`) — configurable `max_chars` / `overlap_chars`, `ChunkConfig`, page-number propagation
- [x] Embedding module (`app/rag/embedder.py`) — `all-MiniLM-L6-v2` via sentence-transformers, lazy-loaded, injectable model for tests
- [x] Pinecone upsert module (`app/rag/pinecone_store.py`) — batched upsert, `VectorIndex` Protocol, metadata per vector
- [x] REST API client (`app/rag/api_client.py`) — document registration, hash-based dedup check, status updates
- [x] End-to-end pipeline (`app/rag/ingestion.py`) — `ingest_document` + `ingest_many`, `pending → processing → indexed | failed` status flow
- [x] `POST /ingest` endpoint (`app/routes/ingest.py`) — Pydantic-validated request, aggregated `IngestionResult` response
- [x] 66 tests across 6 unit test files + 1 integration test file (all mocked: no Pinecone key, no LlamaParse key, no PyTorch required)

### Phase 4: Agent Backend Core — COMPLETE

All Phase 4 tasks (4.1–4.18) are implemented and tested. See [docs/phases/phase_4.md](docs/phases/phase_4.md) for full details.

- [x] LLM Gateway (`app/gateway/client.py`) — Claude API wrapper, configurable model/temperature/max_tokens
- [x] Input sanitizer (`app/gateway/sanitizer.py`) — prompt injection detection (regex patterns)
- [x] PII redactor (`app/pii/redactor.py`) — Presidio-backed, `[ENTITY_TYPE_N]` placeholders, mapping table
- [x] PII re-hydrator (`app/pii/redactor.py`) — access-level-aware: full/restricted/read_only
- [x] Pinecone retriever (`app/retrieval/retriever.py`) — matter_id + access_level metadata filtering
- [x] BGE reranker (`app/retrieval/reranker.py`) — FlagReranker, top-K sorted by score
- [x] Citation formatter (`app/retrieval/citations.py`) — JSONB `[{doc_id, chunk_id, text_snippet, page}]`
- [x] MCP client (`app/mcp_client/client.py`) — HTTP transport calls to Node API MCP tools
- [x] LangGraph retrieval agent (`app/agents/retrieval_agent.py`) — search → rerank → generate → cite
- [x] LangGraph orchestrator (`app/agents/orchestrator.py`) — intent classification → routing
- [x] SSE chat endpoint (`app/routes/chat.py`) — `POST /chat`, token streaming + citations
- [x] PII integrated into chat flow — redact before LLM, re-hydrate by access level
- [x] MongoDB checkpointer (`app/agents/checkpointer.py`) — langgraph-checkpoint-mongodb factory
- [x] LangSmith tracing (`app/agents/tracing.py`) — TracingConfig with env-var setup
- [x] JWT validation in FastAPI (`app/auth/jwt_validator.py`) — HS256, python-jose, require_auth dependency
- [x] Access control wired into /chat — matter assignments → retriever filter
- [x] 145 unit + integration tests (213 total agents tests, all passing)

### Phase 5: Desktop App — COMPLETE

All Phase 5 tasks (5.1–5.15) are implemented and tested. See [docs/phases/phase_5.md](docs/phases/phase_5.md) for full details.

- [x] Zustand auth store (`stores/authStore.ts`) — token, user, login/logout actions
- [x] REST API client (`services/apiClient.ts`) — fetch wrapper with JWT header injection + 401 auto-logout
- [x] Login page (`components/LoginPage/`) — email + password form, JWT stored, redirect on success
- [x] Auth guard (`components/AuthGuard/`) — login page vs main view based on auth state
- [x] Matter selector (`components/MatterSelector/`) — fetches assigned matters, sets active in Zustand
- [x] SSE client service (`services/sseClient.ts`) — POST SSE via fetch + ReadableStream; token + citations events
- [x] Chat input component (`components/Chat/ChatInput.tsx`) — textarea, send button, Enter to send
- [x] Chat message display (`components/Chat/ChatMessage.tsx`) — streaming cursor, citation references
- [x] Inline citation rendering (`components/Citations/CitationLink.tsx`) — numbered `[N]` with hover tooltip
- [x] Conversation list sidebar (`components/ConversationList/`) — list, switch, search
- [x] New conversation action — "New Chat" creates and switches to new conversation
- [x] Document viewer (`components/DocumentViewer/`) — split-view read-only, chunk highlight + scroll
- [x] Document viewer navigation — scrolls to referenced chunk by substring match
- [x] Conversation search — real-time title/content filter
- [x] 73 component + store + service tests (13 files, all passing)

### Phase 6: End-to-End Integration — NOT STARTED

Full vertical slice: login → select matter → ask question → streamed cited response.

### Phase 7: Research & Drafting Agents — NOT STARTED

Research agent (multi-source), drafting agent (template + freeform), document export.

### Phase 8: Desktop Research & Drafting UI — NOT STARTED

### Phase 9: Hardening & Production Readiness — NOT STARTED

SSO/SAML/OIDC, encryption, performance testing, security review.

---

## Spec Coverage Map

Traceability from [spec.md](spec.md) functional requirements to implementation status.

| Requirement | Description | Status |
|-------------|-------------|--------|
| **FR-1** | Chat Assistant | |
| FR-1.1 | Conversational chat interface | Phase 5 |
| FR-1.2 | Stream responses in real-time | Phase 4 |
| FR-1.3 | Inline citations with doc viewer | Phase 5 |
| FR-1.4 | Persist conversations per matter | **Done** (API + schema) |
| **FR-2** | Search & Retrieval | |
| FR-2.1 | Unified search across data | Phase 4 |
| FR-2.2 | DuckDuckGo web search | Phase 7 |
| FR-2.3 | Westlaw/LexisNexis integration | Phase 7 (stub) |
| FR-2.4 | bge-reranker re-ranking | Phase 4 |
| FR-2.5 | Source attribution | Phase 4 |
| **FR-3** | Document Generation | |
| FR-3.1 | Template-based generation | Phase 7 |
| FR-3.2 | Freeform AI drafting | Phase 7 |
| FR-3.3 | DOCX/PDF/Markdown export | Phase 7 |
| **FR-4** | Research & Analysis | |
| FR-4.1 | Multi-step legal research | Phase 7 |
| FR-4.2 | Cross-document synthesis | Phase 7 |
| **FR-5** | Document Ingestion & RAG | |
| FR-5.1 | Auto-ingest on startup/login | **Done** (`POST /ingest` + pipeline) |
| FR-5.2 | Manual refresh | **Done** (`POST /ingest` endpoint) |
| FR-5.3 | Directory sync | Phase 9 (Airflow DAG) |
| FR-5.4 | LlamaParse PDF parsing | **Done** (`app/rag/parser.py`) |
| FR-5.5 | SHA-256 dedup | **Done** (`app/rag/hasher.py` + dedup check) |
| FR-5.6 | Embedding + Pinecone storage | **Done** (`app/rag/embedder.py` + `pinecone_store.py`) |
| FR-5.7 | Airflow re-indexing | Phase 9 |
| **FR-6** | Document Viewer | |
| FR-6.1–6.4 | Split-view read-only viewer | Phase 5 |
| **FR-7** | Access Control & Auth | |
| FR-7.1 | Pluggable auth (SSO + password) | **Done** (password); SSO in Phase 9 |
| FR-7.2 | Matter-level access control | **Done** |
| FR-7.3 | Role-based access control | **Done** |
| FR-7.4 | Consistent across data types | **Done** (API); Agents in Phase 4 |
| **FR-8** | PII Management | |
| FR-8.1 | Redact PII before LLM | Phase 4 |
| FR-8.2 | Redact PII by access level | Phase 4 |
| FR-8.3 | PII audit log | **Done** (schema + service) |
| **FR-9** | Multi-Agent System | |
| FR-9.1 | Orchestrator/router agent | Phase 4 |
| FR-9.2 | Retrieval agent | Phase 4 |
| FR-9.3 | Research agent | Phase 7 |
| FR-9.4 | Drafting agent | Phase 7 |
| FR-9.5 | MongoDB checkpoints | Phase 4 |
| **FR-10** | Structured Data | |
| FR-10.1 | CRUD via Node REST API | **Done** |
| FR-10.2 | MCP server layer | **Done** (10 tools, 25 tests) |
| **FR-11** | LLM Gateway | |
| FR-11.1 | Claude API wrapper | Phase 4 |
| FR-11.2 | Input sanitization | Phase 4 |
| **FR-12** | Observability | |
| FR-12.1 | LangSmith tracing | Phase 4 |

---

## Quick Start

### Prerequisites

- Node.js >= 20
- Python >= 3.12 + [uv](https://github.com/astral-sh/uv)
- Rust + Cargo (for Tauri)
- Docker + Docker Compose

### Infrastructure

```bash
cd infra && docker compose up -d    # Postgres 16 + MongoDB 7
```

### Node REST API

See [api/README.md](api/README.md) for full details.

```bash
cd api
cp .env.example .env
npm install
npx prisma migrate dev
npm run dev                          # http://localhost:3000
```

### Python Agent Backend

See [agents/README.md](agents/README.md) for full details, Makefile targets, and environment variable reference.

```bash
cd agents
uv sync
uv run uvicorn app.main:app --reload  # http://localhost:8000
```

### Desktop App

```bash
cd desktop
npm install
npm run tauri dev                     # Opens native window
```

### Running Tests

```bash
# All workspaces
npm test

# Individual
cd api && npm test
cd agents && uv run pytest
cd desktop && npm test
```

### Linting

```bash
# All workspaces
npm run lint

# Individual
cd api && npm run lint
cd agents && uv run ruff check .
cd desktop && npm run lint
```

---

## Phase Dependency Graph

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 4 (core agents)
                │                        │
                └──► Phase 3 (ingest) ───┘
                                         │
                                    Phase 5 (desktop) ──► Phase 6 (E2E)
                                         │
                                    Phase 7 (research/draft) ──► Phase 8 (desktop R&D UI)
                                                                      │
                                                                 Phase 9 (hardening)
```

**Critical path:** 0 → 1 → 3 + 2 (parallel) → 4 → 5 → 6
