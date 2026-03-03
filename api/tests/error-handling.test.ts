/**
 * Phase 1 — Zod Validation & Global Error Handler Tests (Tasks 1.19, 1.20)
 *
 * ALL TESTS EXPECTED TO FAIL until validation and error handler are implemented.
 *   - Validation tests: routes return 404 (not 400) because routes don't exist
 *   - Error handler tests: unhandled errors aren't formatted yet
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const DOC_ID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
const CONV_ID = 'ffffffff-ffff-ffff-ffff-ffffffffffff'

const { mockPrisma } = vi.hoisted(() => ({
  mockPrisma: {
    matterAssignment: {
      findFirst: vi.fn().mockResolvedValue({
        matter_id: '11111111-1111-1111-1111-111111111111',
        access_level: 'full',
      }),
    },
  },
}))

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

// ─── Task 1.19 — Zod validation (400 responses for invalid payloads) ─────────

describe('Zod validation — POST /auth/register', () => {
  it('returns 400 with structured error when body is empty', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: {},
    })
    expect(response.statusCode).toBe(400)
    const body = response.json<{ message: string; errors?: unknown }>()
    expect(body.message).toBeDefined()
    await app.close()
  })

  it('returns 400 with field-level errors for invalid email format', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: { email: 'not-email', password: 'valid123', name: 'X', role: 'attorney' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when password is too short (< 8 chars)', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: { email: 'a@b.com', password: 'abc', name: 'Test', role: 'attorney' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('Zod validation — POST /auth/login', () => {
  it('returns 400 when email is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { password: 'password123' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when password is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'attorney@firm.com' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('Zod validation — POST /matters', () => {
  it('returns 400 when title is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { case_number: 'CASE-2024-001', status: 'active' },
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
      payload: { title: 'Test Matter', status: 'active' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when status is not a valid enum', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Test Matter', case_number: 'CASE-2024-001', status: 'invalid_status' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('Zod validation — PATCH /documents/:id/status', () => {
  it('returns 400 for status not in DocumentStatus enum', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'PATCH',
      url: `/documents/${DOC_ID}/status`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { status: 'removed' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('Zod validation — POST /conversations/:id/messages', () => {
  it('returns 400 when content is empty string', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/conversations/${CONV_ID}/messages`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { role: 'user', content: '' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

// ─── Task 1.20 — Global error handler ────────────────────────────────────────

describe('Global error handler (Task 1.20)', () => {
  it('returns structured JSON (not a stack trace) for unhandled errors', async () => {
    const app = await buildServer()
    // /error-test is a route that deliberately throws (to be added in task 1.20 setup)
    const response = await app.inject({ method: 'GET', url: '/error-test' })
    // Should return 500 JSON, not a raw stack trace
    expect(response.statusCode).toBe(500)
    const body = response.json<{ message: string; stack?: string }>()
    expect(body.message).toBeDefined()
    expect(body.stack).toBeUndefined()
    await app.close()
  })

  it('returns 404 JSON (not HTML) for unknown routes', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/this-route-does-not-exist' })
    expect(response.statusCode).toBe(404)
    const contentType = response.headers['content-type'] ?? ''
    expect(contentType).toContain('application/json')
    await app.close()
  })
})
