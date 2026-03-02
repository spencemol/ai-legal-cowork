# Legal AI Tool — Node API

REST API backend for the Legal AI Tool, managing client accounts, user authentication, legal matters, documents, conversations, and audit logging.

## Tech Stack

- **Runtime**: Node.js (>=20)
- **Framework**: Fastify 5
- **Language**: TypeScript (strict mode)
- **ORM**: Prisma (PostgreSQL)
- **Auth**: JWT (`@fastify/jwt`) + bcrypt password hashing
- **Validation**: Zod schemas
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
