/**
 * Phase 9 — Task 9.1: SSO / OIDC auth tests
 *
 * Verifies:
 *   - GET /auth/sso/config returns correct structure when SSO is/isn't configured
 *   - POST /auth/sso/callback validates OIDC ID tokens and issues internal JWTs
 *   - Fallback to password auth still works when AUTH_STRATEGY=password
 *   - Invalid tokens produce 401
 *   - Missing SSO config produces 503
 */
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from 'vitest'
import jwt from 'jsonwebtoken'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

// ── Constants ────────────────────────────────────────────────────────────────

const OIDC_SECRET = 'oidc-test-shared-secret-32-chars-!!'
const OIDC_ISSUER = 'https://sso.firm-example.com'
const OIDC_AUDIENCE = 'legal-ai-tool'

// ── Prisma mock ───────────────────────────────────────────────────────────────

const { mockPrisma } = vi.hoisted(() => {
  const baseUser = {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    email: 'sso.user@firm.com',
    name: 'SSO User',
    role: 'attorney',
    password_hash: null,
    sso_provider: 'https://sso.firm-example.com',
    sso_id: 'sso-sub-12345',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }

  return {
    mockPrisma: {
      user: {
        create: vi.fn().mockResolvedValue(baseUser),
        findUnique: vi.fn().mockResolvedValue(null), // default: user not found → auto-provision
        findMany: vi.fn().mockResolvedValue([baseUser]),
        update: vi.fn().mockResolvedValue(baseUser),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () {
    return mockPrisma
  }),
}))

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeOidcToken(
  overrides: Partial<{
    sub: string
    email: string
    name: string
    role: string
    iss: string
    aud: string
    exp: number
  }> = {},
): string {
  const payload = {
    sub: overrides.sub ?? 'sso-sub-12345',
    email: overrides.email ?? 'sso.user@firm.com',
    name: overrides.name ?? 'SSO User',
    role: overrides.role ?? 'attorney',
    iss: overrides.iss ?? OIDC_ISSUER,
    aud: overrides.aud ?? OIDC_AUDIENCE,
  }
  const options: jwt.SignOptions = {
    expiresIn: overrides.exp !== undefined ? undefined : '1h',
  }
  if (overrides.exp !== undefined) {
    // sign without expiresIn, add exp manually
    return jwt.sign({ ...payload, exp: overrides.exp }, OIDC_SECRET)
  }
  return jwt.sign(payload, OIDC_SECRET, options)
}

function setOidcEnv() {
  process.env.OIDC_ISSUER = OIDC_ISSUER
  process.env.OIDC_AUDIENCE = OIDC_AUDIENCE
  process.env.OIDC_SECRET = OIDC_SECRET
  process.env.AUTH_STRATEGY = 'oidc'
}

function clearOidcEnv() {
  delete process.env.OIDC_ISSUER
  delete process.env.OIDC_AUDIENCE
  delete process.env.OIDC_SECRET
  delete process.env.AUTH_STRATEGY
}

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeAll(() => {
  process.env.JWT_SECRET = TEST_SECRET
})

beforeEach(() => {
  vi.clearAllMocks()
  // Default: user not found → auto-provision
  mockPrisma.user.findUnique.mockResolvedValue(null)
  mockPrisma.user.create.mockResolvedValue({
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    email: 'sso.user@firm.com',
    name: 'SSO User',
    role: 'attorney',
    password_hash: null,
    sso_provider: OIDC_ISSUER,
    sso_id: 'sso-sub-12345',
    created_at: new Date(),
    updated_at: new Date(),
  })
})

afterEach(() => {
  clearOidcEnv()
})

// ── GET /auth/sso/config ─────────────────────────────────────────────────────

describe('GET /auth/sso/config', () => {
  it('returns sso_enabled=false when OIDC env vars are not set', async () => {
    clearOidcEnv()
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/sso/config' })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ sso_enabled: boolean; strategy: string }>()
    expect(body.sso_enabled).toBe(false)
    await app.close()
  })

  it('returns sso_enabled=true when OIDC env vars are configured', async () => {
    setOidcEnv()
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/sso/config' })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ sso_enabled: boolean; provider: string; strategy: string }>()
    expect(body.sso_enabled).toBe(true)
    expect(body.provider).toBe(OIDC_ISSUER)
    await app.close()
  })

  it('returns strategy=password when AUTH_STRATEGY is not set', async () => {
    clearOidcEnv()
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/sso/config' })
    const body = response.json<{ strategy: string }>()
    expect(body.strategy).toBe('password')
    await app.close()
  })

  it('returns strategy=oidc when AUTH_STRATEGY=oidc', async () => {
    setOidcEnv()
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/sso/config' })
    const body = response.json<{ strategy: string }>()
    expect(body.strategy).toBe('oidc')
    await app.close()
  })

  it('does not require authentication to call /auth/sso/config', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/auth/sso/config' })
    // Must be accessible without a Bearer token
    expect(response.statusCode).not.toBe(401)
    await app.close()
  })
})

// ── POST /auth/sso/callback ───────────────────────────────────────────────────

describe('POST /auth/sso/callback', () => {
  it('returns 503 when SSO is not configured', async () => {
    clearOidcEnv()
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: 'any-token' },
    })
    expect(response.statusCode).toBe(503)
    await app.close()
  })

  it('returns 400 when id_token is missing from body', async () => {
    setOidcEnv()
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: {},
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })

  it('returns 401 for an invalid/malformed OIDC token', async () => {
    setOidcEnv()
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: 'not.a.valid.token' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 401 for an expired OIDC token', async () => {
    setOidcEnv()
    // exp = 1 (Unix epoch 1970) → definitely expired
    const expiredToken = makeOidcToken({ exp: 1 })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: expiredToken },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 401 for a token signed with wrong secret', async () => {
    setOidcEnv()
    const wrongSecretToken = jwt.sign(
      { sub: 'sub-123', email: 'user@firm.com', iss: OIDC_ISSUER, aud: OIDC_AUDIENCE },
      'wrong-secret',
      { expiresIn: '1h' },
    )
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: wrongSecretToken },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 200 with access_token and refresh_token for valid OIDC token', async () => {
    setOidcEnv()
    const idToken = makeOidcToken()
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: idToken },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ access_token: string; refresh_token: string }>()
    expect(typeof body.access_token).toBe('string')
    expect(typeof body.refresh_token).toBe('string')
    await app.close()
  })

  it('internal JWT contains id, email, role from OIDC claims', async () => {
    setOidcEnv()
    // Return an existing user so findUnique returns something
    mockPrisma.user.findUnique.mockResolvedValueOnce({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      email: 'sso.user@firm.com',
      name: 'SSO User',
      role: 'attorney',
      password_hash: null,
      sso_provider: OIDC_ISSUER,
      sso_id: 'sso-sub-12345',
      created_at: new Date(),
      updated_at: new Date(),
    })

    const idToken = makeOidcToken({ email: 'sso.user@firm.com', role: 'attorney' })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: idToken },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ access_token: string }>()
    const decoded = jwt.verify(body.access_token, TEST_SECRET) as Record<string, unknown>
    expect(decoded.email).toBe('sso.user@firm.com')
    expect(decoded.role).toBe('attorney')
    await app.close()
  })

  it('auto-provisions new SSO user when not found in database', async () => {
    setOidcEnv()
    mockPrisma.user.findUnique.mockResolvedValueOnce(null)
    const idToken = makeOidcToken({ email: 'newuser@sso.com' })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: idToken },
    })
    expect(response.statusCode).toBe(200)
    expect(mockPrisma.user.create).toHaveBeenCalledOnce()
    await app.close()
  })

  it('skips user creation when SSO user already exists', async () => {
    setOidcEnv()
    mockPrisma.user.findUnique.mockResolvedValueOnce({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      email: 'sso.user@firm.com',
      name: 'SSO User',
      role: 'attorney',
      password_hash: null,
      sso_provider: OIDC_ISSUER,
      sso_id: 'sso-sub-12345',
      created_at: new Date(),
      updated_at: new Date(),
    })
    const idToken = makeOidcToken({ email: 'sso.user@firm.com' })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/sso/callback',
      payload: { id_token: idToken },
    })
    expect(response.statusCode).toBe(200)
    expect(mockPrisma.user.create).not.toHaveBeenCalled()
    await app.close()
  })
})

// ── Password auth still works alongside SSO ───────────────────────────────────

describe('Password auth fallback when SSO is configured', () => {
  const CORRECT_PW_HASH = '$2b$10$dIFQ7eVzFe5uxxVpz1AK6O7Z8B2rE5Z.2Z11Zzbwq.cY.Ee3dVuRW'

  it('POST /auth/login still works when AUTH_STRATEGY=oidc', async () => {
    setOidcEnv()
    mockPrisma.user.findUnique.mockResolvedValueOnce({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      email: 'attorney@firm.com',
      name: 'Test Attorney',
      role: 'attorney',
      password_hash: CORRECT_PW_HASH,
      sso_provider: null,
      sso_id: null,
      created_at: new Date(),
      updated_at: new Date(),
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/auth/login',
      payload: { email: 'attorney@firm.com', password: 'correctpassword' },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ access_token: string }>()
    expect(typeof body.access_token).toBe('string')
    await app.close()
  })

  it('GET /auth/me works with password-issued token regardless of SSO config', async () => {
    setOidcEnv()
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/auth/me',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })
})
