# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Legal AI desktop application for law firms. Provides conversational AI chat, unified search and retrieval across structured and unstructured data, legal research, and document generation — all with strict matter-level and role-based access control, PII redaction, and data residency. Each firm self-hosts an isolated single-tenant instance. Desktop only, always-online, English only for v1.

See [spec.md](spec.md) for full functional/non-functional requirements and [plan.md](plan.md) for architecture and implementation roadmap.

## Tech Stack

### Desktop App
- Tauri 2 (Rust backend + web frontend) + React + TypeScript
- Zustand for state management, @tanstack/react-query for data fetching
- SSE for streaming (WebSocket-ready abstraction for future upgrade)

### Agent Backend (Python)
- Python 3.12 + FastAPI + LangGraph (multi-agent orchestration)
- LangSmith for observability and tracing
- LangGraph native MongoDB checkpointer for agent state persistence
- Claude API via LLM Gateway module (input sanitization, prompt injection detection)
- Presidio for PII redaction (local, open-source)
- DuckDuckGo for web search augmentation
- Westlaw/LexisNexis integration (future, for paid legal database research)

### RAG / Ingestion Pipeline
- Pinecone vector DB with metadata filtering for access control
- `all-MiniLM-L6-v2` (sentence-transformers, local) for embeddings
- LlamaParse for PDF parsing and chunking
- SHA-256 hashing for deduplication
- bge-reranker for result re-ranking
- Apache Airflow for re-indexing triggers

### Node REST API
- Node.js + TypeScript (strict mode) + Fastify
- Prisma ORM + Postgres
- JWT authentication, RBAC middleware
- Zod for validation
- MCP server layer on top of REST endpoints

### Document Generation
- Jinja2 templates + python-docx for template-based drafting
- LLM-driven freeform drafting with retrieved context
- Export: DOCX, PDF, Markdown

### Data Stores
- Postgres: users, matters, clients, documents, conversations, audit logs
- MongoDB: LangGraph agent checkpoints
- Pinecone: vector embeddings with matter-level metadata

### Out of Scope (v1)
- Billing and payment processing
- Mobile, multi-language, offline/air-gapped operation
- Real-time collaboration, e-discovery, court e-filing
- Local LLM hosting, document version history, file editing

## Monorepo Structure

```
legal-ai-tool/
├── desktop/          # Tauri 2 app (Rust + React)
├── agents/           # Python agent backend (FastAPI + LangGraph)
├── api/              # Node REST API (Fastify + Prisma)
├── shared/           # Cross-service schemas and constants
├── infra/            # Docker Compose, Airflow DAGs, scripts
```

## Key Commands

### Node REST API (`api/`)
- `make test` — run tests (vitest)
- `make lint` — run linter (eslint)
- `make build` — compile TypeScript
- `make dev` — start dev server

### Python Agent Backend (`agents/`)
- `uvicorn app.main:app` — start dev server

### Desktop App (`desktop/`)
- `cargo tauri dev` — start Tauri dev mode

### Infrastructure
- `docker-compose up` — start Postgres + MongoDB for local dev
