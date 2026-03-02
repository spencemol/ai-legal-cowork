/**
 * Phase 1 — Clients & MatterClients Tests (Task 1.9)
 *
 * ALL TESTS EXPECTED TO FAIL until routes are implemented.
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const CLIENT_ID = 'dddddddd-dddd-dddd-dddd-dddddddddddd'

const { mockPrisma } = vi.hoisted(() => {
  const baseClient = {
    id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
    name: 'Alice Smith',
    email: 'alice@example.com',
    role: 'plaintiff',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }
  const baseMatterClient = {
    id: 'mc-1',
    matter_id: '11111111-1111-1111-1111-111111111111',
    client_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
    linked_at: new Date('2024-01-01T00:00:00Z'),
  }
  return {
    mockPrisma: {
      client: {
        create: vi.fn().mockResolvedValue(baseClient),
        findUnique: vi.fn().mockResolvedValue(baseClient),
        findMany: vi.fn().mockResolvedValue([baseClient]),
        update: vi.fn().mockResolvedValue(baseClient),
      },
      matterClient: {
        create: vi.fn().mockResolvedValue(baseMatterClient),
        delete: vi.fn().mockResolvedValue(baseMatterClient),
        findMany: vi.fn().mockResolvedValue([baseMatterClient]),
      },
      matterAssignment: {
        findFirst: vi.fn().mockResolvedValue({
          matter_id: '11111111-1111-1111-1111-111111111111',
          access_level: 'full',
        }),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () { return mockPrisma }),
}))

beforeAll(() => {
  process.env.JWT_SECRET = TEST_SECRET
})

beforeEach(() => {
  vi.clearAllMocks()
  mockPrisma.matterAssignment.findFirst.mockResolvedValue({
    matter_id: MATTER_ID,
    access_level: 'full',
  })
})

// ─── Task 1.9 — Client CRUD ───────────────────────────────────────────────────

describe('POST /clients', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/clients',
      payload: { name: 'Alice Smith', email: 'alice@example.com', role: 'plaintiff' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 201 with created client', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/clients',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { name: 'Alice Smith', email: 'alice@example.com', role: 'plaintiff' },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; name: string; email: string }>()
    expect(body.name).toBe('Alice Smith')
    expect(body.email).toBe('alice@example.com')
    await app.close()
  })

  it('returns 400 when name is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/clients',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { email: 'alice@example.com', role: 'plaintiff' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('GET /clients/:id', () => {
  it('returns 200 with client data', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/clients/${CLIENT_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ id: string; name: string }>()
    expect(body.id).toBe(CLIENT_ID)
    await app.close()
  })

  it('returns 404 for unknown client', async () => {
    mockPrisma.client.findUnique.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/clients/99999999-9999-9999-9999-999999999999',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(404)
    await app.close()
  })
})

// ─── Task 1.9 — MatterClient link/unlink ─────────────────────────────────────

describe('POST /matters/:matterId/clients', () => {
  it('returns 200 when linking client to matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/clients`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { client_id: CLIENT_ID },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })
})

describe('DELETE /matters/:matterId/clients/:clientId', () => {
  it('returns 204 when unlinking client from matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'DELETE',
      url: `/matters/${MATTER_ID}/clients/${CLIENT_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(204)
    await app.close()
  })
})

describe('GET /matters/:matterId/clients', () => {
  it('returns 200 with list of clients for matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}/clients`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<unknown[]>()
    expect(Array.isArray(body)).toBe(true)
    await app.close()
  })
})
