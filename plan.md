# Legal AI Tool — System Design Plan

## Context

This plan defines the system architecture and implementation roadmap for a Legal AI desktop application for law firms. The tool provides conversational AI, document retrieval (RAG), legal research, and document generation — all with strict access control, PII protection, and data residency. Each firm self-hosts an isolated instance. This is a greenfield project; no code exists yet.

---

## Architecture Overview

### Subsystems

| Subsystem | Tech | Responsibility |
|-----------|------|---------------|
| **Desktop App** | Tauri 2 + React + TypeScript | Chat UI, search, doc viewer, auth flows |
| **Agent Backend** | Python 3.12 + FastAPI + LangGraph | Multi-agent orchestration, RAG, LLM Gateway, PII redaction, doc generation |
| **REST API** | Node.js + TypeScript (strict) + Fastify | Structured data CRUD, auth (JWT), RBAC, MCP server |
| **Ingestion Pipeline** | Python (shared with agent backend) + Airflow | Doc parsing, chunking, embedding, Pinecone indexing |
| **Data Stores** | Postgres, MongoDB, Pinecone | Structured data, agent checkpoints, vector embeddings |

### Communication Patterns

```
Tauri Desktop App (React frontend)
  |
  |-- SSE --> Python Agent Backend (FastAPI)    [chat streaming, search, research]
  |              |
  |              |-- HTTP/REST --> Node REST API  [structured data via MCP]
  |              |-- Local --> Presidio           [PII redaction]
  |              |-- Local --> sentence-transformers (all-MiniLM-L6-v2) [embeddings]
  |              |-- HTTP --> Pinecone            [vector search]
  |              |-- HTTP --> Claude API           [via LLM Gateway module]
  |              |-- HTTP --> DuckDuckGo          [web search]
  |              |-- HTTP --> Westlaw/LexisNexis  [legal DB, future]
  |              |-- MongoDB                       [LangGraph checkpoints]
  |              +-- LangSmith                     [observability]
  |
  +-- HTTP/REST --> Node REST API                 [auth, client/matter CRUD]
                      |
                      +-- Postgres                 [users, matters, clients, audit logs]
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Desktop framework | Tauri 2 | Rust backend + web frontend; mature, small binary |
| Frontend | React + TypeScript | Largest ecosystem, component libraries |
| State management | Zustand | Minimal, fast, great TypeScript support |
| Agent framework | LangGraph + FastAPI | Mature, LangSmith integration, checkpointing |
| Embeddings | all-MiniLM-L6-v2 (local) | Data residency, no external API dependency |
| Streaming | SSE (WebSocket-ready abstraction) | Simple for v1, upgrade path built in |
| Auth | Node REST API owns auth, JWT | Single source of truth in Postgres |
| Node framework | Fastify | Fast, schema-based validation, good TypeScript support |
| Vector ACL | Pinecone metadata filtering | matter_id + access_level per vector |
| MCP | Dual-purpose (agent tools + external) | Unified API surface |
| PII | Presidio (local) | Open-source, local, customizable for legal entities |
| Tenancy | Single-tenant (1 DB per firm) | Matches self-hosted constraint |
| File sync | Manual-only for v1 | Startup ingestion + manual refresh only |
| LLM Gateway | Module in agent backend | Simpler deployment, wraps Claude API |
| Checkpointing | LangGraph native MongoDB checkpointer | Battle-tested, out-of-box resumable workflows |
| Doc templates | Jinja2 + python-docx | Flexible, well-understood, DOCX/PDF/MD export |
| Repo structure | Monorepo | Atomic changes, single CI, easier to keep in sync |
| Service comms | HTTP/REST | Python <-> Node via REST; consistent with MCP layer |

---

## Monorepo Structure

```
legal-ai-tool/
├── desktop/                    # Tauri 2 app
│   ├── src-tauri/              # Rust backend (Tauri commands, file system access)
│   │   ├── src/
│   │   └── Cargo.toml
│   └── src/                    # React frontend
│       ├── components/
│       ├── pages/
│       ├── services/           # API clients (SSE, REST)
│       ├── hooks/
│       └── types/
├── agents/                     # Python agent backend
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint
│   │   ├── agents/             # LangGraph agent definitions
│   │   │   ├── orchestrator.py # Router agent
│   │   │   ├── retrieval.py    # RAG retrieval agent
│   │   │   ├── research.py     # Multi-step research agent
│   │   │   └── drafting.py     # Document generation agent
│   │   ├── gateway/            # LLM Gateway module
│   │   │   ├── client.py       # Claude API wrapper
│   │   │   └── sanitizer.py    # Input sanitization / prompt injection detection
│   │   ├── rag/                # RAG pipeline
│   │   │   ├── embedder.py     # all-MiniLM-L6-v2 embedding
│   │   │   ├── retriever.py    # Pinecone query + metadata filtering
│   │   │   ├── reranker.py     # bge-reranker
│   │   │   └── ingestion.py    # Doc parsing, chunking, dedup
│   │   ├── pii/                # PII redaction
│   │   │   ├── redactor.py     # Presidio integration
│   │   │   └── audit.py        # PII access audit logging
│   │   ├── docgen/             # Document generation
│   │   │   ├── templates/      # Jinja2 templates
│   │   │   ├── renderer.py     # python-docx / PDF / MD rendering
│   │   │   └── freeform.py     # LLM-driven freeform drafting
│   │   ├── mcp_client/         # MCP client for calling Node REST API
│   │   ├── models/             # Pydantic models
│   │   └── config.py           # Configuration
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── api/                        # Node REST API
│   ├── src/
│   │   ├── server.ts           # Fastify entrypoint
│   │   ├── routes/             # REST endpoints
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── models/             # Prisma entities
│   │   ├── middleware/         # Auth, RBAC, error handling
│   │   ├── mcp/               # MCP server implementation
│   │   └── config/
│   ├── prisma/                 # DB schema & migrations
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── shared/                     # Shared schemas, types, constants
│   ├── schemas/                # JSON schemas for cross-service contracts
│   └── constants/
├── infra/                      # Infrastructure config
│   ├── docker-compose.yml      # Local dev: Postgres, MongoDB
│   ├── airflow/                # Airflow DAGs for re-indexing
│   └── scripts/                # Setup, seed, migration scripts
├── .github/                    # CI/CD
├── CLAUDE.md
├── AGENTS.md
└── spec.md
```

---

## Data Models

### Postgres (Node REST API)

```sql
-- Users & Auth
users
  id              UUID PK
  email           VARCHAR UNIQUE
  name            VARCHAR
  role            ENUM('attorney', 'paralegal', 'partner')
  password_hash   VARCHAR (nullable -- null for SSO users)
  sso_provider    VARCHAR (nullable)
  sso_subject_id  VARCHAR (nullable)
  created_at      TIMESTAMP
  updated_at      TIMESTAMP

-- Matters / Cases
matters
  id              UUID PK
  title           VARCHAR
  case_number     VARCHAR UNIQUE
  status          ENUM('active', 'closed', 'archived')
  description     TEXT
  created_at      TIMESTAMP
  updated_at      TIMESTAMP

-- Matter-level access control
matter_assignments
  id              UUID PK
  matter_id       UUID FK -> matters
  user_id         UUID FK -> users
  access_level    ENUM('full', 'restricted', 'read_only')
  assigned_at     TIMESTAMP

-- Clients
clients
  id              UUID PK
  name            VARCHAR
  contact_email   VARCHAR
  contact_phone   VARCHAR
  address         TEXT
  created_at      TIMESTAMP
  updated_at      TIMESTAMP

-- Many-to-many: matters <-> clients
matter_clients
  matter_id       UUID FK -> matters
  client_id       UUID FK -> clients
  role            ENUM('plaintiff', 'defendant', 'third_party', 'other')

-- Document registry (metadata only; files on local filesystem)
documents
  id              UUID PK
  matter_id       UUID FK -> matters
  file_name       VARCHAR
  file_path       VARCHAR
  file_hash       VARCHAR (SHA-256)
  mime_type       VARCHAR
  status          ENUM('pending', 'processing', 'indexed', 'failed')
  indexed_at      TIMESTAMP
  created_at      TIMESTAMP

-- Chat persistence
conversations
  id              UUID PK
  user_id         UUID FK -> users
  matter_id       UUID FK -> matters
  title           VARCHAR
  created_at      TIMESTAMP
  updated_at      TIMESTAMP

messages
  id              UUID PK
  conversation_id UUID FK -> conversations
  role            ENUM('user', 'assistant')
  content         TEXT
  citations       JSONB           -- [{doc_id, chunk_id, text_snippet, page}]
  created_at      TIMESTAMP

-- Audit trail
audit_logs
  id              UUID PK
  user_id         UUID FK -> users
  action          VARCHAR         -- e.g., 'pii_access', 'document_view', 'search'
  resource_type   VARCHAR
  resource_id     VARCHAR
  metadata        JSONB           -- PII fields accessed, redaction details
  ip_address      INET
  created_at      TIMESTAMP
```

### Pinecone Vector Schema

```
Each vector record:
  id:        "{document_id}_{chunk_index}"
  values:    [384-dim float array]  # all-MiniLM-L6-v2 output dimension
  metadata:
    document_id:    UUID
    matter_id:      UUID
    chunk_index:    INT
    chunk_text:     STRING (truncated for Pinecone metadata limits)
    file_name:      STRING
    page_number:    INT (nullable)
    access_level:   STRING          # mirrors matter_assignment access level
    content_type:   STRING          # 'email', 'brief', 'transcript', 'court_record', etc.
```

### MongoDB (Agent Checkpoints)

LangGraph native checkpointer schema (langgraph-checkpoint-mongodb). No custom schema needed. Stores:
- Thread ID -> checkpoint state (agent state, intermediate results, tool call history)
- Enables resumable multi-step workflows after interruption

---

## Multi-Agent Architecture (LangGraph)

```
User Query
    |
    v
+-------------------+
|  Orchestrator      |  Interprets intent, routes to specialist agent
|  (Router Agent)    |
+---+----+----+-----+
    |    |    |
    v    v    v
+------+ +------+ +------+
|Retri-| |Resea-| |Draft-|
|eval  | |rch   | |ing   |
|Agent | |Agent | |Agent |
+------+ +------+ +------+

Retrieval Agent:  Vector search -> re-rank -> return cited chunks
Research Agent:   Multi-step: firm data + DuckDuckGo + legal DBs -> synthesize
Drafting Agent:   Template-based (Jinja2) or freeform (LLM) -> render docs
```

### Agent -> Tool Mapping

| Agent | Tools |
|-------|-------|
| Orchestrator | route_to_retrieval, route_to_research, route_to_drafting, clarify_intent |
| Retrieval | pinecone_search, bge_rerank, format_citations |
| Research | pinecone_search, duckduckgo_search, legal_db_search, synthesize |
| Drafting | get_matter_context (MCP), render_template, llm_draft, export_docx/pdf/md |

### Shared Tools (all agents)

| Tool | Description |
|------|-------------|
| mcp_client | Call Node REST API via MCP for structured data |
| llm_gateway | Send prompts to Claude with sanitization |
| pii_redactor | Redact PII before LLM calls |

---

## PII Redaction Flow

```
1. User query arrives at agent backend
2. Retrieval agent fetches relevant chunks from Pinecone
3. PII Redactor (Presidio) scans chunks:
   a. Detects PII entities (names, SSNs, addresses, phone numbers, etc.)
   b. For LLM context: replaces PII with placeholders ([PERSON_1], [SSN_1])
   c. Maintains a mapping table (placeholder -> original) in memory
4. Redacted chunks sent to Claude via LLM Gateway
5. Claude response received with placeholders
6. For display to user:
   a. Check user's access level for the matter
   b. Re-hydrate placeholders based on access level:
      - full access -> show all PII
      - restricted -> partial redaction
      - read_only -> full redaction
   c. Audit log: record which PII fields were accessed by which user
7. Response streamed to desktop app via SSE
```

---

## Implementation Phases

### Phase 0: Foundation & Scaffolding
- Initialize monorepo structure
- Set up Tauri 2 project with React + TypeScript
- Set up Python project (FastAPI, pyproject.toml, dependencies)
- Set up Node project (TypeScript strict, package.json, Prisma)
- Docker Compose for local dev (Postgres, MongoDB)
- CI pipeline skeleton (lint, type-check, test for all 3 runtimes)

### Phase 1: Auth, RBAC & Structured Data CRUD (Node REST API)
- Postgres schema (Prisma migrations)
- User registration + login (username/password)
- JWT issuance + validation middleware
- RBAC middleware (role-based route guards)
- CRUD endpoints: users, matters, clients, matter_assignments, documents, conversations, messages
- Audit log service
- Zod request validation schemas for all routes
- Global error handler middleware (Fastify `onError` hook)
- **Tests**: Unit tests for auth, RBAC, CRUD, matter-scoped access control

### Phase 2: MCP Server Layer (Node REST API)
- Install `@modelcontextprotocol/sdk`; scaffold MCP server in `api/src/mcp/`
- Register MCP tools for matters, clients, documents, conversations, and audit logging
- **Tests**: Integration tests for MCP tools (mock Prisma, verify tool responses)

### Phase 3: Ingestion Pipeline
- LlamaParse integration for PDF parsing
- Chunking strategy (semantic chunking, configurable chunk size/overlap)
- SHA-256 dedup (hash check before re-embedding)
- all-MiniLM-L6-v2 embedding via sentence-transformers
- Pinecone upsert with metadata (matter_id, access_level, etc.)
- Document status tracking (pending -> processing -> indexed)
- Manual refresh endpoint (user specifies files)
- Startup ingestion trigger
- **Tests**: Unit tests for chunking, dedup, embedding; integration test for end-to-end ingestion

### Phase 4: Agent Backend Core (Minimal Chat Path)
- FastAPI app skeleton with SSE streaming endpoint (`POST /chat`)
- LLM Gateway module (Claude API wrapper, input sanitization, prompt injection detection)
- Presidio PII redactor + re-hydrator (access-level-aware; custom recognizers for legal entities)
- Pinecone retriever with metadata filtering (matter_id, access_level)
- bge-reranker integration + citation formatter
- MCP client for calling Node REST API
- LangGraph orchestrator agent (intent classification, routing) + retrieval agent (search -> rerank -> cite)
- LangGraph MongoDB checkpointer setup
- LangSmith integration (tracing)
- JWT validation in FastAPI; matter-scoped access wired into `/chat`
- **Tests**: Unit tests for gateway, PII redactor, retriever; integration tests for agent workflows

### Phase 5: Desktop App (Minimal Usable Client)
- Tauri 2 shell with React frontend
- Auth flow (login screen -> JWT storage in Tauri secure store) + auth guard
- Zustand store (auth slice); REST API client with JWT header injection
- Chat interface (message input, streaming response display, conversation list)
- SSE client service (with abstraction layer for future WebSocket upgrade)
- Inline citation rendering (clickable links with snippet preview)
- Split-view document viewer (read-only, navigates to chunk/section)
- Matter selector / context switcher
- **Tests**: Component tests (React Testing Library)

### Phase 6: End-to-End Integration (Minimal Vertical Slice)
- Add agents backend to `docker-compose.yml`; configure shared JWT secret
- Seed script: test user, matter, assignment, sample PDF → Postgres + Pinecone
- E2E smoke test: login → select matter → ask question → streamed cited response
- E2E test: citation click → document viewer opens at correct section
- E2E test: cross-matter access control (user without assignment → 403 / empty results)
- E2E test: PII redacted in LLM trace, re-hydrated per access level in response
- E2E test: conversation persisted and resumable across sessions
- E2E test: audit log records PII access events

### Phase 7: Research & Drafting Agents
- Research agent (multi-step: firm data + DuckDuckGo + legal DB stubs); wire into orchestrator
- Drafting agent — template-based (Jinja2 + python-docx); wire into orchestrator
- Drafting agent — freeform (LLM-driven with retrieved context)
- Export pipeline (DOCX, PDF via pandoc/weasyprint, Markdown)
- **Tests**: Agent workflow tests (research + drafting paths), document generation tests

### Phase 8: Desktop App — Research & Drafting UI
- Research results display with mixed citation source-type badges (internal, web, legal DB)
- Document generation request UI (template selector or freeform, format selector DOCX/PDF/MD)
- Document download handler (save generated file to local disk via Tauri)
- **Tests**: Component tests for research display and document generation UI

### Phase 9: Hardening, Observability & Production Readiness
- Pluggable SSO/SAML/OIDC auth (configurable per deployment); SSO login flow in desktop
- Encryption at rest for Postgres; enforce HTTPS/TLS for all inter-service communication
- Airflow DAG for scheduled re-indexing
- Custom Presidio recognizers for legal entities (case numbers, bar IDs, court names)
- Prompt injection detection test suite (known attack patterns blocked)
- Performance tests: 200 concurrent users on `/chat`; retrieval across 100K+ vectors
- Security tests: cross-matter data leakage, privilege escalation, audit log completeness
- **Tests**: Load tests, security tests, E2E audit log completeness

---

## Dependencies & Execution Order

```
Phase 0 ──→ Phase 1 ──→ Phase 2 (MCP) ──→ Phase 4 (agents)
                │                               │
                └──→ Phase 3 (ingest) ──────────┘
                                                │
                                           Phase 5 (desktop) ──→ Phase 6 (E2E)
                                                │
                                           Phase 7 (research/draft) ──→ Phase 8 (desktop R&D UI)
                                                                               │
                                                                          Phase 9 (hardening)
```

- Phase 1 and Phase 3 can run **in parallel** after Phase 0
- Phase 2 (MCP) depends on Phase 1 (CRUD endpoints must exist before wrapping as MCP tools)
- Phase 4 depends on Phase 2 (MCP client needs tools registered) and Phase 3 (retrieval needs indexed docs)
- Phase 5 depends on Phase 1 (auth) and Phase 4 (agent streaming)
- Phase 6 depends on Phases 1–5
- Phase 7 depends on Phase 4 (agent framework must exist)
- Phase 8 depends on Phase 5 (desktop shell) and Phase 7 (research/drafting agents)
- Phase 9 depends on all prior phases

---

## Key Dependencies (Libraries)

### Python (agents/)
- fastapi, uvicorn -- HTTP server
- langgraph, langchain-core, langchain-anthropic -- agent framework
- langsmith -- observability
- langgraph-checkpoint-mongodb -- checkpointing
- pinecone-client -- vector DB
- sentence-transformers -- embeddings (all-MiniLM-L6-v2)
- FlagEmbedding -- bge-reranker
- presidio-analyzer, presidio-anonymizer -- PII
- llama-parse -- PDF parsing
- python-docx -- DOCX generation
- jinja2 -- templating
- httpx -- async HTTP client (for MCP/REST calls)
- duckduckgo-search -- web search

### Node (api/)
- fastify -- HTTP server
- prisma -- ORM + migrations
- jsonwebtoken, bcrypt -- auth
- zod -- validation
- @modelcontextprotocol/sdk -- MCP server

### Rust/React (desktop/)
- tauri 2.x -- desktop framework
- react 18+, typescript -- frontend
- @tanstack/react-query -- data fetching
- zustand -- state management

---

## Verification

### How to test end-to-end
1. Start infrastructure: `docker-compose up` (Postgres, MongoDB)
2. Run Node API: `cd api && npm run dev`
3. Run Python agents: `cd agents && uvicorn app.main:app`
4. Run Tauri desktop: `cd desktop && cargo tauri dev`
5. Create a test user and matter via REST API
6. Ingest sample legal documents (PDFs) via manual refresh
7. Open desktop app, log in, select matter
8. Ask a question -> verify streaming response with citations
9. Click citation -> verify doc viewer opens at correct section
10. Verify PII redaction in LangSmith traces
11. Verify audit log entries in Postgres
12. Test RBAC: log in as different roles, verify visibility restrictions
