/**
 * Phase 1 — Auth Tests (Tasks 1.2, 1.3, 1.4, 1.5, 1.6)
 *
 * ALL TESTS EXPECTED TO FAIL until routes and services are implemented.
 *   - Route tests fail because /auth/register, /auth/login, /auth/me do not exist → 404
 *   - Unit tests fail because src/auth/password.ts does not exist → module not found
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, signToken, TEST_SECRET } from './helpers/token'
import jwt from 'jsonwebtoken'

// --- Prisma mock (hoisted so factory can close over it) ---
const { mockPrisma } = vi.hoisted(() => {
  // Pre-computed bcrypt hash of 'correctpassword' (rounds=10) for login tests
  const CORRECT_PW_HASH = '$2b$10$dIFQ7eVzFe5uxxVpz1AK6O7Z8B2rE5Z.2Z11Zzbwq.cY.Ee3dVuRW'

  const baseUser = {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    email: 'attorney@firm.com',
    name: 'Test Attorney',
    role: 'attorney',
    password_hash: CORRECT_PW_HASH,
    sso_provider: null,
    sso_id: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }

  const baseMatter = {
    id: '11111111-1111-1111-1111-111111111111',
    name: 'Test Matter',
    status: 'active',
    created_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }

  return {
    mockPrisma: {
      user: {
        // Returns the input data merged with defaults so email echoes back correctly
        create: vi.fn().mockImplementation(
          async ({ data }: { data: Record<string, unknown> }) => ({
            ...baseUser,
            ...data,
          }),
        ),
        findUnique: vi.fn().mockResolvedValue(baseUser),
        findMany: vi.fn().mockResolvedValue([baseUser]),
        update: vi.fn().mockResolvedValue(baseUser),
      },
      matter: {
        create: vi.fn().mockResolvedValue(baseMatter),
        findUnique: vi.fn().mockResolvedValue(baseMatter),
        findMany: vi.fn().mockResolvedValue([baseMatter]),
        update: vi.fn().mockResolvedValue(baseMatter),
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
})

// ─── Task 1.2 — POST /auth/register ──────────────────────────────────────────

describe('POST /auth/register', () => {
  it('returns 201 with user object (no password_hash)', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: {
        email: 'newuser@firm.com',
        password: 'SecurePass123!',
        name: 'New User',
        role: 'attorney',
      },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; email: string; password_hash?: string }>()
    expect(body.email).toBe('newuser@firm.com')
    expect(body.password_hash).toBeUndefined()
    await app.close()
  })

  it('returns 409 when email already exists', async () => {
    mockPrisma.user.create.mockRejectedValueOnce(
      Object.assign(new Error('Unique constraint violation'), { code: 'P2002' }),
    )
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: {
        email: 'attorney@firm.com',
        password: 'SecurePass123!',
        name: 'Duplicate',
        role: 'attorney',
      },
    })
    expect(response.statusCode).toBe(409)
    await app.close()
  })

  it('returns 400 when email is malformed', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: {
        email: 'not-an-email',
        password: 'SecurePass123!',
        name: 'Bad Email',
        role: 'attorney',
      },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when required fields are missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: { email: 'test@firm.com' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 400 when role is not a valid enum value', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/register',
      payload: {
        email: 'test@firm.com',
        password: 'SecurePass123!',
        name: 'Test',
        role: 'superadmin',
      },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

// ─── Task 1.3 — POST /auth/login ─────────────────────────────────────────────

describe('POST /auth/login', () => {
  it('returns 200 with access_token and refresh_token for valid credentials', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'attorney@firm.com', password: 'correctpassword' },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ access_token: string; refresh_token: string }>()
    expect(typeof body.access_token).toBe('string')
    expect(typeof body.refresh_token).toBe('string')
    // JWT payload should contain id, email, role
    const decoded = jwt.verify(body.access_token, TEST_SECRET) as Record<string, unknown>
    expect(decoded.email).toBe('attorney@firm.com')
    expect(decoded.role).toBe('attorney')
    await app.close()
  })

  it('returns 401 for wrong password', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'attorney@firm.com', password: 'wrongpassword' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 401 for unknown email', async () => {
    mockPrisma.user.findUnique.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'nobody@firm.com', password: 'anypassword' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 400 when body is missing', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'POST', url: '/auth/login', payload: {} })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

// ─── Task 1.4 — JWT validation middleware ────────────────────────────────────

describe('GET /auth/me (JWT middleware)', () => {
  it('returns 401 when no Authorization header is present', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/me' })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 200 with user context when valid Bearer token is provided', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/auth/me',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ id: string; email: string; role: string }>()
    expect(body.id).toBe(TEST_USERS.attorney.id)
    expect(body.email).toBe(TEST_USERS.attorney.email)
    expect(body.role).toBe('attorney')
    await app.close()
  })

  it('returns 401 for a tampered token', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/auth/me',
      headers: { authorization: 'Bearer invalidtoken.abc.xyz' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 401 for an expired token', async () => {
    const expired = jwt.sign(
      { id: TEST_USERS.attorney.id, email: TEST_USERS.attorney.email, role: 'attorney' },
      TEST_SECRET,
      { expiresIn: '-1s' },
    )
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/auth/me',
      headers: { authorization: `Bearer ${expired}` },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })
})

// ─── Task 1.5 — RBAC middleware ──────────────────────────────────────────────
// Tested via POST /matters which only attorneys and partners can create.
// A paralegal token should receive 403.

describe('RBAC middleware (via POST /matters)', () => {
  it('returns 403 when paralegal attempts a partner/attorney-only action', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { name: 'Test Matter', status: 'active' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('allows attorney to perform attorney-level actions', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { name: 'Test Matter', status: 'active' },
    })
    // 201 Created (not 403 Forbidden)
    expect(response.statusCode).toBe(201)
    await app.close()
  })

  it('allows partner to perform any attorney-level action', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.partner) },
      payload: { name: 'Partner Matter', status: 'active' },
    })
    expect(response.statusCode).toBe(201)
    await app.close()
  })
})

// ─── Task 1.6 — Auth service unit tests ──────────────────────────────────────
// Import the password utilities that will live at src/auth/password.ts.
// This import will fail until task 1.2 is implemented.

describe('Auth service unit tests (src/auth/password.ts)', () => {
  it('hashPassword returns a bcrypt hash that is not the plain password', async () => {
    const { hashPassword } = await import('../src/auth/password')
    const hash = await hashPassword('mypassword')
    expect(typeof hash).toBe('string')
    expect(hash).not.toBe('mypassword')
    expect(hash.startsWith('$2')).toBe(true)
  })

  it('verifyPassword returns true for matching password and hash', async () => {
    const { hashPassword, verifyPassword } = await import('../src/auth/password')
    const hash = await hashPassword('mypassword')
    const result = await verifyPassword('mypassword', hash)
    expect(result).toBe(true)
  })

  it('verifyPassword returns false for wrong password', async () => {
    const { hashPassword, verifyPassword } = await import('../src/auth/password')
    const hash = await hashPassword('mypassword')
    const result = await verifyPassword('wrongpassword', hash)
    expect(result).toBe(false)
  })
})

// Ensure token helper signs tokens with correct structure
describe('signToken (helper sanity check)', () => {
  it('generates a valid JWT with id, email, role in payload', () => {
    const token = signToken(TEST_USERS.attorney)
    const decoded = jwt.verify(token, TEST_SECRET) as Record<string, unknown>
    expect(decoded.id).toBe(TEST_USERS.attorney.id)
    expect(decoded.email).toBe(TEST_USERS.attorney.email)
    expect(decoded.role).toBe('attorney')
  })
})
