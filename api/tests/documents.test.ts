/**
 * Phase 1 — Documents Tests (Tasks 1.13, 1.14)
 *
 * ALL TESTS EXPECTED TO FAIL until routes are implemented.
 *   - Schema task 1.13 has no test file (migration is the verifiable outcome)
 *   - Route tests fail because /documents endpoints do not exist → 404
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const DOC_ID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'

const { mockPrisma } = vi.hoisted(() => {
  const baseDocument = {
    id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    matter_id: '11111111-1111-1111-1111-111111111111',
    file_name: 'contract.pdf',
    file_path: '/uploads/contract.pdf',
    file_size: 204800,
    mime_type: 'application/pdf',
    sha256_hash: 'abc123deadbeef',
    status: 'pending',
    uploaded_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }
  return {
    mockPrisma: {
      document: {
        create: vi.fn().mockResolvedValue(baseDocument),
        findUnique: vi.fn().mockResolvedValue(baseDocument),
        findMany: vi.fn().mockResolvedValue([baseDocument]),
        update: vi.fn().mockResolvedValue({ ...baseDocument, status: 'indexed' }),
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
    user_id: TEST_USERS.attorney.id,
    access_level: 'full',
  })
})

// ─── Task 1.14 — Document CRUD routes ────────────────────────────────────────

describe('POST /matters/:matterId/documents', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/documents`,
      payload: {
        file_name: 'contract.pdf',
        file_path: '/uploads/contract.pdf',
        file_size: 204800,
        mime_type: 'application/pdf',
        sha256_hash: 'abc123deadbeef',
      },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 201 with registered document metadata', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: {
        file_name: 'contract.pdf',
        file_path: '/uploads/contract.pdf',
        file_size: 204800,
        mime_type: 'application/pdf',
        sha256_hash: 'abc123deadbeef',
      },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; file_name: string; status: string }>()
    expect(body.id).toBeDefined()
    expect(body.file_name).toBe('contract.pdf')
    expect(body.status).toBe('pending')
    await app.close()
  })

  it('returns 400 when required fields are missing', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { file_name: 'contract.pdf' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})

describe('GET /matters/:matterId/documents', () => {
  it('returns 200 with list of documents for the matter', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<unknown[]>()
    expect(Array.isArray(body)).toBe(true)
    await app.close()
  })

  it('returns 403 when user is not assigned to the matter', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}/documents`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })
})

describe('GET /documents/:id', () => {
  it('returns 200 with document data', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/documents/${DOC_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ id: string; file_name: string; status: string }>()
    expect(body.id).toBe(DOC_ID)
    await app.close()
  })

  it('returns 404 for unknown document', async () => {
    mockPrisma.document.findUnique.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/documents/99999999-9999-9999-9999-999999999999',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(404)
    await app.close()
  })
})

describe('PATCH /documents/:id/status', () => {
  it('returns 200 with updated status', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'PATCH',
      url: `/documents/${DOC_ID}/status`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { status: 'indexed' },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{ status: string }>()
    expect(body.status).toBe('indexed')
    await app.close()
  })

  it('returns 400 for invalid status value', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'PATCH',
      url: `/documents/${DOC_ID}/status`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { status: 'deleted' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})
