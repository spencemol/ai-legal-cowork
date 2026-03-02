/**
 * Phase 1 — Conversations & Messages Tests (Tasks 1.15, 1.16)
 *
 * ALL TESTS EXPECTED TO FAIL until routes are implemented.
 *   - Schema task 1.15 has no test file (migration is the verifiable outcome)
 *   - Route tests fail because /conversations endpoints do not exist → 404
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { buildServer } from '../src/server'
import { TEST_USERS, bearerHeader, TEST_SECRET } from './helpers/token'

const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const CONV_ID = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
const MSG_ID = '00000000-0000-0000-0000-000000000001'

const { mockPrisma } = vi.hoisted(() => {
  const baseConversation = {
    id: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
    matter_id: '11111111-1111-1111-1111-111111111111',
    title: 'Analysis of contract clause 7',
    created_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
    messages: [],
  }
  const baseMessage = {
    id: '00000000-0000-0000-0000-000000000001',
    conversation_id: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
    role: 'user',
    content: 'What does clause 7 say about indemnification?',
    citations: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
  }
  return {
    mockPrisma: {
      conversation: {
        create: vi.fn().mockResolvedValue(baseConversation),
        findUnique: vi.fn().mockResolvedValue({ ...baseConversation, messages: [baseMessage] }),
        findMany: vi.fn().mockResolvedValue([baseConversation]),
      },
      message: {
        create: vi.fn().mockResolvedValue(baseMessage),
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
  PrismaClient: vi.fn(() => mockPrisma),
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

// ─── Task 1.16 — Conversation CRUD routes ────────────────────────────────────

describe('POST /matters/:matterId/conversations', () => {
  it('returns 401 without auth', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/conversations`,
      payload: { title: 'New conversation' },
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 201 with created conversation', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/conversations`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { title: 'Analysis of contract clause 7' },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; matter_id: string; title: string }>()
    expect(body.id).toBeDefined()
    expect(body.matter_id).toBe(MATTER_ID)
    expect(body.title).toBe('Analysis of contract clause 7')
    await app.close()
  })

  it('returns 403 when user is not assigned to the matter', async () => {
    mockPrisma.matterAssignment.findFirst.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/matters/${MATTER_ID}/conversations`,
      headers: { authorization: bearerHeader(TEST_USERS.paralegal) },
      payload: { title: 'Unauthorized conversation' },
    })
    expect(response.statusCode).toBe(403)
    await app.close()
  })
})

describe('GET /matters/:matterId/conversations', () => {
  it('returns 200 with list of conversations', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/matters/${MATTER_ID}/conversations`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<unknown[]>()
    expect(Array.isArray(body)).toBe(true)
    await app.close()
  })
})

describe('GET /conversations/:id', () => {
  it('returns 200 with full conversation including messages', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: `/conversations/${CONV_ID}`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(200)
    const body = response.json<{
      id: string
      messages: Array<{ id: string; role: string; content: string }>
    }>()
    expect(body.id).toBe(CONV_ID)
    expect(Array.isArray(body.messages)).toBe(true)
    await app.close()
  })

  it('returns 404 for unknown conversation', async () => {
    mockPrisma.conversation.findUnique.mockResolvedValueOnce(null)
    const app = await buildServer()
    const response = await app.inject({
      method: 'GET',
      url: '/conversations/99999999-9999-9999-9999-999999999999',
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
    })
    expect(response.statusCode).toBe(404)
    await app.close()
  })
})

describe('POST /conversations/:id/messages', () => {
  it('returns 201 with created message', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/conversations/${CONV_ID}/messages`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: {
        role: 'user',
        content: 'What does clause 7 say about indemnification?',
      },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ id: string; role: string; content: string; citations: unknown }>()
    expect(body.id).toBeDefined()
    expect(body.role).toBe('user')
    await app.close()
  })

  it('returns 201 with assistant message including citations JSONB', async () => {
    const citations = [
      {
        doc_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
        chunk_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee_0',
        text_snippet: 'The indemnifying party shall hold harmless...',
        page: 12,
        file_name: 'contract.pdf',
        source_type: 'internal',
      },
    ]
    mockPrisma.message.create.mockResolvedValueOnce({
      id: MSG_ID,
      conversation_id: CONV_ID,
      role: 'assistant',
      content: 'Clause 7 addresses indemnification as follows...',
      citations,
      created_at: new Date(),
    })
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/conversations/${CONV_ID}/messages`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: {
        role: 'assistant',
        content: 'Clause 7 addresses indemnification as follows...',
        citations,
      },
    })
    expect(response.statusCode).toBe(201)
    const body = response.json<{ citations: unknown[] }>()
    expect(Array.isArray(body.citations)).toBe(true)
    expect(body.citations).toHaveLength(1)
    await app.close()
  })

  it('returns 400 for invalid role value', async () => {
    const app = await buildServer()
    const response = await app.inject({
      method: 'POST',
      url: `/conversations/${CONV_ID}/messages`,
      headers: { authorization: bearerHeader(TEST_USERS.attorney) },
      payload: { role: 'system', content: 'Do something bad' },
    })
    expect(response.statusCode).toBe(400)
    await app.close()
  })
})
