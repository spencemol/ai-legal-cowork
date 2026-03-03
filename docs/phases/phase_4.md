# Phase 4 — Agent Backend Core: Implementation Report

## 1. Summary of What Was Implemented

Phase 4 delivers the **minimal AI chat path**: a user query flows through the LangGraph orchestrator to the retrieval agent, which searches Pinecone, re-ranks results, formats citations, and streams the answer back via SSE. All PII is redacted before reaching the LLM and re-hydrated according to user access level. JWT validation and matter-scoped access control protect the `/chat` endpoint.

### New Modules (agents/)

| Module | File | Description |
|--------|------|-------------|
| LLM Gateway | `app/gateway/client.py` | `LLMGateway` wraps Anthropic `AsyncAnthropic`; configurable model, temperature, max_tokens, system prompt |
| Input Sanitizer | `app/gateway/sanitizer.py` | `InputSanitizer` detects prompt injection patterns (system override, role-play attacks, ignore-previous) |
| PII Redactor | `app/pii/redactor.py` | `PIIRedactor` (Presidio-backed, injectable engines, lazy init); `PIIRehydrator` (access-level-aware restore: full/restricted/read_only) |
| PII Audit | `app/pii/audit.py` | `PIIAuditLogger` records PII access events |
| Pinecone Retriever | `app/retrieval/retriever.py` | `PineconeRetriever` queries by embedding + metadata filter (matter_id, access_level) |
| BGE Reranker | `app/retrieval/reranker.py` | `BGEReranker` wraps `FlagReranker`; sorts by score descending, returns top-K |
| Citation Formatter | `app/retrieval/citations.py` | `CitationFormatter` converts ranked chunks → `[{doc_id, chunk_id, text_snippet, page}]` JSONB schema |
| MCP Client | `app/mcp_client/client.py` | `MCPClient` calls Node REST API tools via HTTP (httpx); supports `get_matter`, `list_matters`, `get_matter_assignments` |
| Retrieval Agent | `app/agents/retrieval_agent.py` | LangGraph `StateGraph`; nodes: retrieve → rerank → generate → format_citations |
| Orchestrator Agent | `app/agents/orchestrator.py` | LangGraph `StateGraph`; intent classification → routes to retrieval or general answer |
| Checkpointer | `app/agents/checkpointer.py` | `MongoCheckpointerFactory` wraps `langgraph-checkpoint-mongodb` with env-driven config |
| LangSmith Tracing | `app/agents/tracing.py` | `TracingConfig` dataclass + `configure_tracing()` sets env vars for LangSmith |
| JWT Validator | `app/auth/jwt_validator.py` | `JWTValidator` decodes HS256 tokens (python-jose); `require_auth` FastAPI dependency |
| Chat Endpoint | `app/routes/chat.py` | `POST /chat` SSE endpoint (sse-starlette); streams tokens + final citations JSON event |

### Updated

- `app/main.py` — registers `chat_router` alongside `ingest_router`
- `pyproject.toml` — added Phase 4 dependencies: `anthropic`, `langchain-anthropic`, `langgraph`, `langchain-core`, `langsmith`, `presidio-analyzer`, `presidio-anonymizer`, `sse-starlette`, `python-jose[cryptography]`

---

## 2. Per-Task Confidence Scores

| Task | Description | Confidence | Notes |
|------|-------------|-----------|-------|
| 4.1 | LLM Gateway — Claude API wrapper | **0.90** | Wraps `AsyncAnthropic` with configurable model/temp/max_tokens; streaming not tested end-to-end against real API (mocked) |
| 4.2 | Input sanitizer — prompt injection detection | **0.88** | Regex patterns cover common injection attempts (system override, role-play, ignore-prev); no ML-based detection |
| 4.3 | Presidio PII redactor | **0.85** | Full `[ENTITY_TYPE_N]` placeholder format with mapping table; graceful degradation when spaCy models absent; production requires `en_core_web_lg` |
| 4.4 | PII re-hydrator — access-level-aware | **0.90** | `full` → all PII restored; `restricted` → sensitive types (SSN, PHONE, EMAIL) remain redacted; `read_only` → all redacted |
| 4.5 | Pinecone retriever with metadata filtering | **0.88** | `matter_id` + `access_level` filter passed as Pinecone metadata filter dict; embedder injected for testability |
| 4.6 | BGE reranker | **0.85** | `FlagReranker` wrapped; computes `(query, chunk_text)` score pairs; optional extra (`agents`); injectable for tests |
| 4.7 | Citation formatter | **0.92** | Output matches `messages.citations` JSONB schema `[{doc_id, chunk_id, text_snippet, page}]` exactly |
| 4.8 | MCP client (HTTP transport) | **0.85** | `httpx.AsyncClient` calls Node API `/mcp` endpoint; tool call + parse pattern; base URL from env |
| 4.9 | LangGraph retrieval agent | **0.87** | `StateGraph` with `RetrievalState`; retrieve → rerank → generate → cite nodes; mocked deps pass all tests |
| 4.10 | LangGraph orchestrator agent | **0.85** | Intent classification (keyword + LLM fallback); routes to retrieval vs. general; routing decision logged |
| 4.11 | FastAPI SSE `/chat` endpoint | **0.88** | `EventSourceResponse` streams tokens + final `citations` event; JWT-protected; matter_id param required |
| 4.12 | PII redaction integrated into chat flow | **0.83** | Redaction before LLM call wired; re-hydration on output by access_level; LangSmith trace verifiable |
| 4.13 | MongoDB checkpointer setup | **0.82** | `MongoCheckpointerFactory` creates `langgraph-checkpoint-mongodb` checkpointer; optional extra; tested with mocked `MongoClient` |
| 4.14 | LangSmith tracing integration | **0.80** | `TracingConfig` sets `LANGCHAIN_TRACING_V2` + `LANGCHAIN_PROJECT` + `LANGCHAIN_API_KEY`; actual dashboard verification requires live key |
| 4.15 | JWT validation in FastAPI | **0.92** | HS256 decode (python-jose); `require_auth` FastAPI dependency; 401 on missing/invalid/expired tokens |
| 4.16 | Access control wired into `/chat` | **0.85** | Extracts matter assignments via MCP client or JWT claims; passes `matter_id` + `access_level` to retriever filter |
| 4.17 | Unit tests for gateway, PII, retriever, reranker | **0.93** | 145 tests across 12 test files; all pass (213 total); no external keys required |
| 4.18 | Integration test — full chat flow | **0.85** | 6 integration tests mock Claude + Pinecone + MCP; full flow: JWT → orchestrator → retrieval → SSE response with citations |

**Average task confidence: 0.867**

---

## 3. Overall Phase 4 Confidence Score

**Overall Phase Score: 0.85 / 1.0**

### Rationale

**Strengths:**
- All 18 tasks have corresponding test coverage (145 new tests, all passing)
- TDD red-green cycle completed for each task
- Core data path (query → orchestrate → retrieve → rerank → cite → stream) is fully exercised
- JWT validation, access control, PII redaction/rehydration, and citation formatting match spec exactly
- All tests fully mocked — no external API keys required

**Gaps (factors reducing confidence below 1.0):**
- **PII**: Presidio requires `en_core_web_lg` spaCy model for production; graceful degradation in place but not production-verified
- **MongoDB checkpointer**: `langgraph-checkpoint-mongodb` in optional extra; not tested against running MongoDB
- **LangSmith tracing**: Env-var configuration only; actual trace visibility requires live LANGSMITH_API_KEY
- **MCP client HTTP transport**: Tested with mocked httpx; not tested against running Node API
- **SSE streaming**: Token-by-token streaming logic tested with mock; actual real-time streaming not E2E verified until Phase 6
- **bge-reranker** (`FlagEmbedding`): Optional extra; tests mock `FlagReranker` — production requires model download

---

## 4. Cumulative Build Summary (Phases 0–4)

### What We Have Built

| Layer | Status | Details |
|-------|--------|---------|
| **Infrastructure** | ✅ COMPLETE | Docker Compose: Postgres 16 + MongoDB 7 |
| **Node REST API** | ✅ COMPLETE | Fastify + Prisma: auth, RBAC, CRUD for all 9 entities, audit log, Zod validation, global error handler |
| **MCP Server Layer** | ✅ COMPLETE | 10 tools (matters, clients, documents, conversations, audit); 25 integration tests |
| **Ingestion Pipeline** | ✅ COMPLETE | LlamaParse → chunker → embedder (all-MiniLM-L6-v2) → Pinecone upsert; SHA-256 dedup; `POST /ingest` |
| **LLM Gateway** | ✅ COMPLETE | Claude API wrapper; configurable model/temp/max_tokens; prompt injection detection |
| **PII Redaction** | ✅ COMPLETE | Presidio-backed; `[ENTITY_TYPE_N]` placeholders; access-level-aware rehydration (full/restricted/read_only) |
| **Vector Retrieval** | ✅ COMPLETE | Pinecone retriever with matter_id + access_level metadata filtering |
| **BGE Reranker** | ✅ COMPLETE | `FlagReranker`-backed; returns top-K scored chunks |
| **Citation Formatter** | ✅ COMPLETE | Produces `messages.citations` JSONB-compatible citation arrays |
| **MCP Client (Python)** | ✅ COMPLETE | HTTP-based MCP tool calls from Python agents to Node API |
| **LangGraph Agents** | ✅ COMPLETE | Orchestrator (intent classification + routing) + Retrieval agent (search → rerank → cite) |
| **SSE Chat Endpoint** | ✅ COMPLETE | `POST /chat` with JWT auth, matter-scoped access control, streaming response + citations |
| **MongoDB Checkpointer** | ✅ COMPLETE | `langgraph-checkpoint-mongodb` factory with env-driven config |
| **LangSmith Tracing** | ✅ COMPLETE | Env-var-based `TracingConfig`; all LangGraph runs and LLM calls traced when configured |
| **Desktop App** | ⏳ NOT STARTED | Phase 5 |
| **E2E Integration** | ⏳ NOT STARTED | Phase 6 |
| **Research/Drafting Agents** | ⏳ NOT STARTED | Phase 7 |

### Test Coverage

| Suite | Files | Tests |
|-------|-------|-------|
| API (Node) | 10 | 113 |
| Agents — Ingestion (Phase 3) | 8 | 68 |
| Agents — Phase 4 | 12 | 145 |
| Desktop | 1 | 1 |
| **Total** | **31** | **327** |

### Spec Coverage After Phase 4

| Requirement | Status |
|-------------|--------|
| FR-1.2 Stream responses | ✅ SSE endpoint |
| FR-2.1 Unified search | ✅ Pinecone retriever + metadata filter |
| FR-2.4 bge-reranker | ✅ BGEReranker |
| FR-2.5 Source attribution | ✅ Citation formatter |
| FR-7.1 Auth (password) | ✅ JWT validation in FastAPI |
| FR-7.2 Matter-level access | ✅ Wired into /chat |
| FR-8.1 PII before LLM | ✅ PIIRedactor in chat flow |
| FR-8.2 PII by access level | ✅ PIIRehydrator |
| FR-9.1 Orchestrator agent | ✅ LangGraph orchestrator |
| FR-9.2 Retrieval agent | ✅ LangGraph retrieval agent |
| FR-9.5 MongoDB checkpoints | ✅ Checkpointer factory |
| FR-10.2 MCP tools (Python client) | ✅ MCPClient |
| FR-11.1 LLM Gateway | ✅ LLMGateway |
| FR-11.2 Input sanitization | ✅ InputSanitizer |
| FR-12.1 LangSmith tracing | ✅ TracingConfig |
