/**
 * Phase 1 — Matter Assignments Tests (Task 1.10)
 *
 * ALL TESTS EXPECTED TO FAIL until routes are implemented.
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const ASSIGNEE_ID = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'

const { mockPrisma } = vi.hoisted(() => {
  const baseAssignment = {
    id: 'assign-1',
    matter_id: '11111111-1111-1111-1111-111111111111',
    user_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    access_level: 'full',
    assigned_at: new Date('2024-01-01T00:00:00Z'),
    user: {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      name: 'Test Paralegal',
      email: 'paralegal@firm.com',
      role: 'paralegal',
    },
  }
  return {
    mockPrisma: {
      matterAssignment: {
        create: vi.fn().mockResolvedValue(baseAssignment),
        findMany: vi.fn().mockResolvedValue([baseAssignment]),
        findFirst: vi.fn().mockResolvedValue(baseAssignment),
        delete: vi.fn().mockResolvedValue(baseAssignment),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(() => mockPrisma),
}))

beforeAll(() => {
  process.env.JWT_SECRET = TEST_SECRET
})

beforeEach(() => {
  vi.clearAllMocks()
  // Default: the requesting user (attorney) is assigned to the matter
  mockPrisma.matterAssignment.findFirst.mockResolvedValue({
    matter_id: '11111111-1111-1111-1111-111111111111',
    user_id: TEST_USERS.attorney.id,
    access_level: 'full',
  })
})

// ─── Task 1.10 — Matter assignment routes ────────────────────────────────────

describe('POST /matters/:id/assignments', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      payload: { user_id: ASSIGNEE_ID, access_level: 'full' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 403 for paralegal (only attorney/partner can assign)', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { user_id: ASSIGNEE_ID, access_level: 'full' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 201 with created assignment for attorney', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { user_id: ASSIGNEE_ID, access_level: 'full' },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{
      matter_id: string
      user_id: string
      access_level: string
    }>()
    expect(body.matter_id).toBe(MATTER_ID)
    expect(body.user_id).toBe(ASSIGNEE_ID)
    expect(body.access_level).toBe('full')
    await app.close()
  })

  it('returns 400 for invalid access_level', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { user_id: ASSIGNEE_ID, access_level: 'superuser' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('GET /matters/:id/assignments', () => {
  it('returns 200 with list of assignments', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<unknown[]>()
    expect(Array.isArray(body)).toBe(true)
    expect(body.length).toBeGreaterThan(0)
    await app.close()
  })
})

describe('DELETE /matters/:id/assignments/:userId', () => {
  it('returns 204 on successful removal', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'DELETE',
      url: `/matters/${MATTER_ID}/assignments/${ASSIGNEE_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(204)
    await app.close()
  })
})
