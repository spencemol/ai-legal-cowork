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
│   │   ├── schemas/             # Zod validation schemas
│   │   └── services/
│   │       └── audit.ts         # Audit log service
│   ├── tests/                   # Vitest test suite (9 test files)
│   ├── prisma/
│   │   └── schema.prisma        # 9 models, 6 enums
│   ├── Makefile                 # make test, make lint, make test-watch, etc.
│   └── Dockerfile
├── agents/                      # Python agent backend (FastAPI)
│   ├── app/
│   │   └── main.py              # FastAPI scaffold + /health
│   ├── tests/
│   │   └── test_health.py       # Health check tests
│   ├── pyproject.toml
│   └── Dockerfile
├── desktop/                     # Tauri 2 + React desktop app
│   ├── src/
│   │   ├── main.tsx             # React entry
│   │   ├── App.tsx              # Root component (scaffold)
│   │   └── App.test.tsx         # Component test
│   ├── src-tauri/               # Rust backend
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

---

## Test Coverage

### API (`api/tests/`) — 9 test files

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

### Agents (`agents/tests/`) — 1 test file

| Test File | Coverage |
|-----------|----------|
| `test_health.py` | FastAPI health endpoint |

### Desktop (`desktop/src/`) — 1 test file

| Test File | Coverage |
|-----------|----------|
| `App.test.tsx` | Root component render |

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

### Phase 2: MCP Server Layer — NOT STARTED

Expose structured data through MCP for the Python agent backend.

- [ ] MCP server scaffold (`@modelcontextprotocol/sdk`)
- [ ] MCP tools for matters, clients, documents, conversations
- [ ] MCP tool for audit logging
- [ ] Integration tests for MCP tools

### Phase 3: Ingestion Pipeline — NOT STARTED

Parse, chunk, embed, and index documents into Pinecone.

- [ ] SHA-256 file hasher, LlamaParse parser, semantic chunker
- [ ] Embedding module (all-MiniLM-L6-v2)
- [ ] Pinecone upsert with metadata
- [ ] Dedup check + document status tracking
- [ ] End-to-end ingestion wiring
- [ ] Manual refresh endpoint

### Phase 4: Agent Backend Core — NOT STARTED

Minimal AI chat path: orchestrator → retrieval agent → cited answer via SSE.

- [ ] LLM Gateway (Claude API wrapper + input sanitization)
- [ ] PII redactor (Presidio) + re-hydrator
- [ ] Pinecone retriever + bge-reranker
- [ ] LangGraph agents (orchestrator + retrieval)
- [ ] SSE streaming endpoint
- [ ] MongoDB checkpointer + LangSmith integration

### Phase 5: Desktop App — NOT STARTED

Chat UI, SSE streaming, citation rendering, document viewer.

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
| FR-5.1 | Auto-ingest on startup/login | Phase 3 |
| FR-5.2 | Manual refresh | Phase 3 |
| FR-5.3 | Directory sync | Phase 3 |
| FR-5.4 | LlamaParse PDF parsing | Phase 3 |
| FR-5.5 | SHA-256 dedup | Phase 3 |
| FR-5.6 | Embedding + Pinecone storage | Phase 3 |
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
| FR-10.2 | MCP server layer | Phase 2 |
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
