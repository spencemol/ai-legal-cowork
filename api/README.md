# Legal AI Tool — Node API

REST API backend for the Legal AI Tool, managing client accounts, user authentication, legal matters, documents, conversations, and audit logging.

## Tech Stack

- **Runtime**: Node.js (>=20)
- **Framework**: Fastify 5
- **Language**: TypeScript (strict mode)
- **ORM**: Prisma (PostgreSQL)
- **Auth**: JWT (`@fastify/jwt`) + bcrypt password hashing
- **Validation**: Zod schemas
- **MCP**: `@modelcontextprotocol/sdk` v1.27 (`McpServer`, `InMemoryTransport`)
- **Testing**: Vitest 4
- **Linting**: ESLint + Prettier

## Getting Started

### Prerequisites

- Node.js >= 20
- PostgreSQL instance
- npm (workspace-aware — this package lives under the root monorepo)

### Setup

```bash
# From repo root
npm install

# Copy env and configure
cp api/.env.example api/.env

# Run Prisma migrations
cd api && npx prisma migrate dev
```

### Environment Variables

| Variable       | Description                       | Default                         |
|----------------|-----------------------------------|---------------------------------|
| `DATABASE_URL` | PostgreSQL connection string      | —                               |
| `PORT`         | Server listen port                | `3000`                          |
| `HOST`         | Server bind address               | `0.0.0.0`                       |
| `JWT_SECRET`   | Secret for signing JWTs           | —                               |

## Commands

All commands can be run via npm scripts or the Makefile:

| Make target    | npm equivalent       | Description                        |
|----------------|----------------------|------------------------------------|
| `make build`   | `npm run build`      | Compile TypeScript to `dist/`      |
| `make dev`     | `npm run dev`        | Start dev server with hot-reload   |
| `make lint`    | `npm run lint`       | Run ESLint                         |
| `make lint-fix`| `npm run lint:fix`   | Run ESLint with auto-fix           |
| `make format`  | `npm run format`     | Format code with Prettier          |
| `make test`    | `npm run test`       | Run tests once                     |
| `make test-watch` | `npm run test:watch` | Run tests in watch mode        |

## Project Structure

```
api/
  src/
    server.ts             # Fastify server factory + entry point
    db.ts                 # Prisma client singleton
    auth/
      password.ts         # bcrypt hash/verify utilities
    middleware/
      authenticate.ts     # JWT verification middleware
      rbac.ts             # Role-based access control
      matterAccess.ts     # Matter-scoped access control
    routes/
      auth.ts             # POST /auth/register, /auth/login, GET /auth/me
      matters.ts          # CRUD /matters, assignments, matter-scoped sub-resources
      clients.ts          # CRUD /clients, matter-client linking
      documents.ts        # CRUD /matters/:id/documents, /documents/:id
      conversations.ts    # CRUD /matters/:id/conversations, /conversations/:id, messages
    schemas/
      auth.ts             # Zod schemas for auth payloads
      matters.ts          # Zod schemas for matter payloads
      documents.ts        # Zod schemas for document payloads
      conversations.ts    # Zod schemas for conversation/message payloads
    services/
      audit.ts            # Audit log writer (prisma.auditLog.create)
    mcp/
      server.ts           # createMcpServer() — McpServer factory, all tools registered
      tools/
        matters.ts        # get_matter · list_matters · get_matter_assignments
        clients.ts        # get_client · list_clients_for_matter
        documents.ts      # list_documents_for_matter · get_document
        conversations.ts  # get_conversation · save_message
        audit.ts          # log_audit_event
    types/
      fastify.d.ts        # Fastify type augmentations
  tests/
    helpers/
      token.ts            # JWT test helpers and fixture users
    health.test.ts        # Server bootstrap sanity
    auth.test.ts          # Auth routes + password service
    matters.test.ts       # Matter CRUD + access control
    clients.test.ts       # Client CRUD + matter linking
    documents.test.ts     # Document CRUD
    conversations.test.ts # Conversation + message CRUD
    assignments.test.ts   # Matter assignment routes
    error-handling.test.ts # Zod validation + global error handler
    audit.test.ts         # Audit log service
    mcp-tools.test.ts     # MCP tool integration tests (Tasks 2.1–2.7)
  prisma/
    schema.prisma         # Database schema (PostgreSQL)
```

## Data Model

The Prisma schema defines the following core entities:

- **User** — attorneys, paralegals, partners (role-based)
- **Matter** — legal cases/matters with status tracking
- **Client** — parties involved in matters (plaintiff, defendant, etc.)
- **MatterAssignment** — user-to-matter access with access levels (full, restricted, read_only)
- **MatterClient** — client-to-matter linkage
- **Document** — file metadata with SHA-256 dedup hashing and processing status
- **Conversation** — AI chat threads scoped to matters
- **Message** — conversation messages with optional JSONB citations
- **AuditLog** — immutable action log for compliance

## Auth & Access Control

1. **JWT Authentication** — all protected routes require a `Bearer` token in the `Authorization` header
2. **RBAC** — role hierarchy: `partner > attorney > paralegal`. Partners can create matters; paralegals cannot
3. **Matter-scoped access** — users must be assigned to a matter to access its resources. Partners bypass this check. Access levels (`full`, `restricted`, `read_only`) control write permissions

---

## MCP Server Layer (Phase 2)

The MCP server exposes the Node API's structured data as **Model Context Protocol tools** so the Python agent backend can call them from LangGraph agents. It uses `McpServer` from `@modelcontextprotocol/sdk` v1.27 with Zod-typed input schemas.

### Architecture

```
Python Agent Backend (LangGraph)
  └── MCP Client (agents/app/mcp_client/)
        │
        │  [InMemoryTransport in tests / StreamableHTTP in production]
        │
        └── McpServer  (api/src/mcp/server.ts)
              ├── tools/matters.ts       — matter queries
              ├── tools/clients.ts       — client queries
              ├── tools/documents.ts     — document registry
              ├── tools/conversations.ts — conversation persistence
              └── tools/audit.ts         — audit log writes
```

**Entry point**: `createMcpServer()` in `src/mcp/server.ts` returns a fully configured `McpServer` instance ready to attach to any MCP transport. The caller owns the transport lifecycle.

### Registered Tools

| Tool | Input | Description |
|------|-------|-------------|
| `get_matter` | `{ id }` | Retrieve a matter by UUID. Returns 404-style `isError` if not found. |
| `list_matters` | `{}` | Return all matters as a JSON array. |
| `get_matter_assignments` | `{ matter_id }` | Assignments for a matter, including nested `user` object. |
| `get_client` | `{ id }` | Retrieve a client by UUID. Returns `isError` if not found. |
| `list_clients_for_matter` | `{ matter_id }` | Clients linked to a matter via `MatterClient`, including nested `client` object. |
| `list_documents_for_matter` | `{ matter_id }` | All documents registered to a matter (metadata + status). |
| `get_document` | `{ id }` | Retrieve a document record by UUID. Returns `isError` if not found. |
| `get_conversation` | `{ id }` | Conversation with full `messages` array included. Returns `isError` if not found. |
| `save_message` | `{ conversation_id, role, content, citations? }` | Persist a new message. `citations` is an optional JSON-stringified array. Returns the new `Message` record. |
| `log_audit_event` | `{ user_id, action, resource_type, resource_id, metadata?, ip_address? }` | Write an audit log entry. `metadata` is an optional JSON-stringified object. Returns the new `AuditLog` record. |

### Tool Response Format

All tools return MCP `content` blocks. On success:

```json
{ "content": [{ "type": "text", "text": "<JSON-serialised result>" }] }
```

On failure (not found, unexpected error):

```json
{ "content": [{ "type": "text", "text": "<error message>" }], "isError": true }
```

### Design Decisions

- **`McpServer` over low-level `Server`** — the high-level API validates inputs with Zod schemas automatically, eliminating boilerplate request dispatching and reducing error surface.
- **Zod input schemas** — each tool declares its input schema as a Zod raw shape, giving the agent backend automatic validation and letting the tool callback receive already-typed arguments.
- **JSON-serialised text responses** — MCP `TextContent` carries the full Prisma record as JSON. The consuming agent parses it and uses it as structured context for LLM prompts.
- **Optional JSON strings for `citations` / `metadata`** — MCP tool arguments are JSON primitives; nested objects are encoded as JSON strings by the caller and `JSON.parse()`d inside the tool, keeping the schema simple and avoiding schema nesting complexity.
- **Stateless per-call** — no session state is held by the MCP server. Each tool call is independent. Conversation and audit state lives in Postgres via Prisma.
- **TypeScript paths in tsconfig** — because `moduleResolution: Node` does not understand package.json `exports` fields, `tsconfig.json` and `tsconfig.test.json` both include a `paths` entry mapping `@modelcontextprotocol/sdk/*` to the installed CJS dist tree. Vitest resolves at runtime via package `exports` without needing the alias.

### Testing Strategy

Tests live in `tests/mcp-tools.test.ts` and use `InMemoryTransport.createLinkedPair()` to wire a real `Client` to the `McpServer` in-process. No network I/O is required.

```
createMcpServer()  ──serverTransport──  McpServer
                                            ↑ registers all tools
test Client  ──clientTransport──────────────┘
  │
  ├── client.listTools()          → verify all 10 tools registered + have descriptions
  ├── client.callTool(name, args) → verify Prisma is called correctly
  └── mockPrisma.*.mockResolvedValue → control return data without a real database
```

**Prisma mock pattern** (consistent with Phase 1 tests):

```typescript
const { mockPrisma } = vi.hoisted(() => ({
  mockPrisma: {
    matter: { findUnique: vi.fn(), findMany: vi.fn() },
    // ... all models used by MCP tools
  },
}))
vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () { return mockPrisma }),
}))
```

`beforeEach` restores default mock return values so each test starts with known data; individual tests override with `mockResolvedValueOnce` for error-path scenarios.

**Test coverage** (25 tests across 7 describe blocks):

| Describe | Tests |
|----------|-------|
| Task 2.1 — Scaffold | server instantiates; connects and responds to `listTools` |
| Task 2.2 — Matter tools | list includes tools; `get_matter` happy path; `get_matter` 404; `list_matters`; assignments with user |
| Task 2.3 — Client tools | list includes tools; `get_client` happy path; `get_client` 404; `list_clients_for_matter` |
| Task 2.4 — Document tools | list includes tools; `list_documents_for_matter`; `get_document` happy path; `get_document` 404 |
| Task 2.5 — Conversation tools | list includes tools; `get_conversation` with messages; `get_conversation` 404; `save_message`; `save_message` with citations |
| Task 2.6 — Audit tool | list includes tool; `log_audit_event`; with optional metadata + IP |
| Task 2.7 — Integration | all 10 tools present; every tool has a description and inputSchema |
