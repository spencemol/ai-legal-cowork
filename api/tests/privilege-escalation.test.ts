/**
 * Phase 9 — Task 9.11: Privilege escalation security tests
 *
 * Verifies that a paralegal token cannot perform partner/attorney-only actions:
 *   - POST /matters (requires attorney|partner)
 *   - PUT /matters/:id with write access
 *   - POST /matters/:id/assignments (requires attorney|partner)
 *   - DELETE /matters/:id/assignments/:userId (requires attorney|partner)
 *   - POST /matters/:id/documents (requires write matter access, not just read_only)
 *
 * Also verifies:
 *   - Partner CAN perform all attorney-level actions
 *   - Attorney CAN perform attorney-level actions
 *   - Paralegal CAN perform read-only actions (GET)
 *   - Role is checked in JWT payload (not in DB)
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'

const { mockPrisma } = vi.hoisted(() => {
  const baseMatter = {
    id: '11111111-1111-1111-1111-111111111111',
    title: 'Smith v. Jones',
    case_number: 'CASE-2024-001',
    description: null,
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
  const baseDoc = {
    id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
    matter_id: '11111111-1111-1111-1111-111111111111',
    file_name: 'contract.pdf',
    file_path: '/files/contract.pdf',
    file_size: 102400,
    mime_type: 'application/pdf',
    status: 'pending',
    uploaded_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
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
      document: {
        create: vi.fn().mockResolvedValue(baseDoc),
        findUnique: vi.fn().mockResolvedValue(baseDoc),
        findMany: vi.fn().mockResolvedValue([baseDoc]),
        update: vi.fn().mockResolvedValue(baseDoc),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () {
    return mockPrisma
  }),
}))

beforeAll(() => {
  process.env.JWT_SECRET = TEST_SECRET
})

beforeEach(() => {
  vi.clearAllMocks()
  // Default: user IS assigned with full access
  mockPrisma.matterAssignment.findFirst.mockResolvedValue({
    id: 'assign-1',
    matter_id: MATTER_ID,
    user_id: TEST_USERS.attorney.id,
    access_level: 'full',
  })
})

// ── Paralegal cannot perform attorney-only write actions ──────────────────────

describe('Paralegal — blocked from attorney/partner-only actions (Task 9.11)', () => {
  it('returns 403 when paralegal attempts POST /matters', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { title: 'Escalation Test', case_number: 'ESC-001', status: 'active' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 403 when paralegal with read_only access attempts PUT /matters/:id', async () => {
    // Paralegal has read_only matter access
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce({
      id: 'assign-para',
      matter_id: MATTER_ID,
      user_id: TEST_USERS.paralegal.id,
      access_level: 'read_only',
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'PUT',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { title: 'Sneaky Update' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 403 when paralegal attempts POST /matters/:id/assignments', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { user_id: 'ffffffff-ffff-ffff-ffff-ffffffffffff', access_level: 'full' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 403 when paralegal attempts DELETE /matters/:id/assignments/:userId', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'DELETE',
      url: `/matters/${MATTER_ID}/assignments/${TEST_USERS.attorney.id}`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })

  it('returns 403 when paralegal with read_only access attempts POST /matters/:id/documents', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce({
      id: 'assign-para',
      matter_id: MATTER_ID,
      user_id: TEST_USERS.paralegal.id,
      access_level: 'read_only',
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: {
        file_name: 'escalation.pdf',
        file_path: '/files/escalation.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
      },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })
})

// ── Paralegal CAN perform read-only actions ───────────────────────────────────

describe('Paralegal — allowed read-only actions (Task 9.11)', () => {
  it('returns 200 when paralegal reads GET /matters with auth', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })

  it('returns 200 when paralegal reads GET /matters/:id (with assignment)', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce({
      id: 'assign-para',
      matter_id: MATTER_ID,
      user_id: TEST_USERS.paralegal.id,
      access_level: 'read_only',
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })
})

// ── Attorney CAN perform attorney-level actions ───────────────────────────────

describe('Attorney — allowed attorney-level actions (Task 9.11)', () => {
  it('returns 201 when attorney creates a matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Attorney Matter', case_number: 'ATT-001', status: 'active' },
    })
    expect(response.statusCode).toBe(201)
    await app.close()
  })

  it('returns 200 when attorney updates a matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'PUT',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Updated Title' },
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })
})

// ── Partner CAN do everything ─────────────────────────────────────────────────

describe('Partner — allowed all attorney-level actions (Task 9.11)', () => {
  it('returns 201 when partner creates a matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      headers: { authorization: bearerHeader(TEST_USERS.partner) },
      payload: { title: 'Partner Matter', case_number: 'PAR-001', status: 'active' },
    })
    expect(response.statusCode).toBe(201)
    await app.close()
  })

  it('returns 201 when partner adds a matter assignment', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/assignments`,
      headers: { authorization: bearerHeader(TEST_USERS.partner) },
      payload: { user_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', access_level: 'full' },
    })
    expect(response.statusCode).toBe(201)
    await app.close()
  })

  it('returns non-403 when partner accesses any matter (global access)', async () => {
    // Partner bypasses matter assignment check
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.partner) },
    })
    expect(response.statusCode).not.toBe(403)
    await app.close()
  })
})

// ── Unauthenticated requests are always rejected ──────────────────────────────

describe('Unauthenticated access — all routes return 401 (Task 9.11)', () => {
  it('GET /matters returns 401 without token', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: '/matters' })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('POST /matters returns 401 without token', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: '/matters',
      payload: { title: 'Unauth', case_number: 'UNAUTH-001', status: 'active' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('GET /matters/:id returns 401 without token', async () => {
    const app = await buildServer()
    const response = await app.inject({ method: 'GET', url: `/matters/${MATTER_ID}` })
    expect(response.statusCode).toBe(401)
    await app.close()
  })
})
