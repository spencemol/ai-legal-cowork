/**
 * Phase 1 — Matters Tests (Tasks 1.8, 1.11, 1.12)
 *
 * ALL TESTS EXPECTED TO FAIL until routes are implemented.
 *   - Routes do not exist → Fastify returns 404 → status code assertions fail
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader } from './helpers/token'
import { TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const OTHER_MATTER_ID = '22222222-2222-2222-2222-222222222222'

const { mockPrisma } = vi.hoisted(() => {
  const baseMatter = {
    id: '11111111-1111-1111-1111-111111111111',
    title: 'Smith v. Jones',
    case_number: 'CASE-2024-001',
    description: 'Contract dispute between Smith and Jones',
    status: 'active',
    created_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }
  const baseAssignment = {
    id: 'assign-1',
    matter_id: '11111111-1111-1111-1111-111111111111',
    user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    access_level: 'full',
    assigned_at: new Date('2024-01-01T00:00:00Z'),
  }
  return {
    mockPrisma: {
      matter: {
        create: vi.fn().mockResolvedValue(baseMatter),
        findUnique: vi.fn().mockResolvedValue(baseMatter),
        findMany: vi.fn().mockResolvedValue([baseMatter]),
        update: vi.fn().mockResolvedValue({ ...baseMatter, title: 'Updated Matter' }),
      },
      matterAssignment: {
        findFirst: vi.fn().mockResolvedValue(baseAssignment),
        findMany: vi.fn().mockResolvedValue([baseAssignment]),
        create: vi.fn().mockResolvedValue(baseAssignment),
        delete: vi.fn().mockResolvedValue(baseAssignment),
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
  // Default: attorney IS assigned to MATTER_ID
  mockPrisma.matterAssignment.findFirst.mockResolvedValue({
    id: 'assign-1',
    matter_id: MATTER_ID,
    user_id: TEST_USERS.attorney.id,
    access_level: 'full',
  })
})

// ─── Task 1.8 — CRUD routes for matters ──────────────────────────────────────

describe('POST /matters', () => {
  it('returns 401 when no auth token is provided', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      payload: { name: 'Smith v. Jones', status: 'active' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 201 with created matter for attorney', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Smith v. Jones', case_number: 'CASE-2024-001', status: 'active' },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; title: string; case_number: string; status: string }>()
    expect(body.id).toBeDefined()
    expect(body.title).toBe('Smith v. Jones')
    expect(body.case_number).toBe('CASE-2024-001')
    await app.close()
  })

  it('returns 400 when title is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { case_number: 'CASE-2024-002', status: 'active' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when case_number is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Smith v. Jones', status: 'active' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('GET /matters', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/matters' })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 200 with array of matters for authenticated user', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<unknown[]>()
    expect(Array.isArray(body)).toBe(true)
    await app.close()
  })
})

describe('GET /matters/:id', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: `/matters/${MATTER_ID}` })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 200 when user is assigned to the matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ id: string; title: string; case_number: string }>()
    expect(body.id).toBe(MATTER_ID)
    expect(body.title).toBeDefined()
    expect(body.case_number).toBeDefined()
    await app.close()
  })

  it('returns 404 when matter does not exist', async () => {
    mockPrisma.matter.findUnique.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/matters/99999999-9999-9999-9999-999999999999',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(404)
    await app.close()
  })
})

describe('PUT /matters/:id', () => {
  it('returns 200 with updated matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'PUT',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Updated Matter' },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ title: string }>()
    expect(body.title).toBe('Updated Matter')
    await app.close()
  })
})

// ─── Tasks 1.11 & 1.12 — Matter-scoped access control ───────────────────────

describe('Matter-scoped access middleware', () => {
  it('returns 403 when user is NOT assigned to the requested matter', async () => {
    // Override: no assignment found for OTHER_MATTER_ID
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${OTHER_MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 200 when user IS assigned to the matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })

  it('restricts document listing to assigned users only', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${OTHER_MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('restricts conversation listing to assigned users only', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${OTHER_MATTER_ID}/conversations`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('partner can access any matter regardless of direct assignment', async () => {
    // Partners bypass matter-scoped check
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${OTHER_MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.partner) },
    })
    // Should not be 403 — partner has global access
    expect(response.statusCode).not.toBe(403)
    await app.close()
  })

  it('access level read_only cannot update a matter', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce({
      matter_id: MATTER_ID,
      user_id: TEST_USERS.paralegal.id,
      access_level: 'read_only',
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'PUT',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { name: 'Sneaky Update' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })
})
