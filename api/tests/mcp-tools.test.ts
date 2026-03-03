/**
 * Phase 2 — MCP Server Layer Integration Tests (Tasks 2.1 – 2.7)
 *
 * ALL TESTS EXPECTED TO FAIL until src/mcp/server.ts and its tools are
 * implemented (module not found → import error → every test fails).
 *
 * Strategy: InMemoryTransport from @modelcontextprotocol/sdk pairs a real
 * Client with a real McpServer in-process, with Prisma mocked via vi.mock.
 */
import { describe, it, expect, vi, beforeEach, beforeAll, afterAll } from 'vitest'
import { Client } from '@modelcontextprotocol/sdk/client'
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory'
import { createMcpServer } from '../src/mcp/server'

// ── Fixtures ──────────────────────────────────────────────────────────────────
const MATTER_ID = '11111111-1111-1111-1111-111111111111'
const OTHER_MATTER_ID = '99999999-9999-9999-9999-999999999999'
const CLIENT_ID = '22222222-2222-2222-2222-222222222222'
const DOC_ID = '33333333-3333-3333-3333-333333333333'
const CONV_ID = '44444444-4444-4444-4444-444444444444'
const MSG_ID = '55555555-5555-5555-5555-555555555555'
const USER_ID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

// ── Prisma mock (hoisted so vi.mock factory can reference it) ─────────────────
const { mockPrisma } = vi.hoisted(() => {
  const baseMatter = {
    id: '11111111-1111-1111-1111-111111111111',
    title: 'Smith v. Jones',
    case_number: 'CASE-2024-001',
    description: 'Contract dispute',
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
    user: {
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      email: 'attorney@firm.com',
      name: 'Test Attorney',
      role: 'attorney',
    },
  }

  const baseClient = {
    id: '22222222-2222-2222-2222-222222222222',
    name: 'John Smith',
    contact_email: 'john@example.com',
    contact_phone: '555-1234',
    address: '123 Main St',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  }

  const baseDocument = {
    id: '33333333-3333-3333-3333-333333333333',
    matter_id: '11111111-1111-1111-1111-111111111111',
    file_name: 'contract.pdf',
    file_path: '/docs/contract.pdf',
    file_size: 1024,
    mime_type: 'application/pdf',
    sha256_hash: 'abc123def456',
    status: 'indexed',
    uploaded_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
    indexed_at: new Date('2024-01-01T00:00:00Z'),
  }

  const baseConversation = {
    id: '44444444-4444-4444-4444-444444444444',
    matter_id: '11111111-1111-1111-1111-111111111111',
    title: 'Research query',
    created_by_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
    messages: [
      {
        id: '55555555-5555-5555-5555-555555555555',
        conversation_id: '44444444-4444-4444-4444-444444444444',
        role: 'user',
        content: 'What is the status?',
        citations: null,
        created_at: new Date('2024-01-01T00:00:00Z'),
      },
    ],
  }

  const baseMessage = {
    id: '55555555-5555-5555-5555-555555555555',
    conversation_id: '44444444-4444-4444-4444-444444444444',
    role: 'assistant',
    content: 'Here is the answer.',
    citations: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
  }

  const baseAuditLog = {
    id: 'audit-log-1',
    user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    action: 'document_view',
    resource_type: 'document',
    resource_id: '33333333-3333-3333-3333-333333333333',
    metadata: { fields: ['name'] },
    ip_address: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
  }

  return {
    mockPrisma: {
      matter: {
        findUnique: vi.fn().mockResolvedValue(baseMatter),
        findMany: vi.fn().mockResolvedValue([baseMatter]),
      },
      matterAssignment: {
        findMany: vi.fn().mockResolvedValue([baseAssignment]),
      },
      client: {
        findUnique: vi.fn().mockResolvedValue(baseClient),
      },
      matterClient: {
        findMany: vi.fn().mockResolvedValue([
          {
            matter_id: '11111111-1111-1111-1111-111111111111',
            client_id: '22222222-2222-2222-2222-222222222222',
            client: baseClient,
          },
        ]),
      },
      document: {
        findUnique: vi.fn().mockResolvedValue(baseDocument),
        findMany: vi.fn().mockResolvedValue([baseDocument]),
      },
      conversation: {
        findUnique: vi.fn().mockResolvedValue(baseConversation),
      },
      message: {
        create: vi.fn().mockResolvedValue(baseMessage),
      },
      auditLog: {
        create: vi.fn().mockResolvedValue(baseAuditLog),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () {
    return mockPrisma
  }),
}))

// ── Helper: parse the first text block from a tool result ─────────────────────
function parseToolText(content: unknown[]): unknown {
  const block = content[0] as { type: string; text: string }
  expect(block.type).toBe('text')
  return JSON.parse(block.text)
}

// ── Helper: create a connected client + server pair ───────────────────────────
async function createTestPair(): Promise<{ client: Client; server: ReturnType<typeof createMcpServer> }> {
  const server = createMcpServer()
  const client = new Client({ name: 'test-client', version: '1.0.0' })
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair()
  await server.connect(serverTransport)
  await client.connect(clientTransport)
  return { client, server }
}

beforeEach(() => {
  vi.clearAllMocks()

  // Restore default mock return values after clearAllMocks
  mockPrisma.matter.findUnique.mockResolvedValue({
    id: MATTER_ID,
    title: 'Smith v. Jones',
    case_number: 'CASE-2024-001',
    description: 'Contract dispute',
    status: 'active',
    created_by_id: USER_ID,
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  })
  mockPrisma.matter.findMany.mockResolvedValue([
    {
      id: MATTER_ID,
      title: 'Smith v. Jones',
      case_number: 'CASE-2024-001',
      description: 'Contract dispute',
      status: 'active',
      created_by_id: USER_ID,
      created_at: new Date('2024-01-01T00:00:00Z'),
      updated_at: new Date('2024-01-01T00:00:00Z'),
    },
  ])
  mockPrisma.matterAssignment.findMany.mockResolvedValue([
    {
      id: 'assign-1',
      matter_id: MATTER_ID,
      user_id: USER_ID,
      access_level: 'full',
      assigned_at: new Date('2024-01-01T00:00:00Z'),
      user: { id: USER_ID, email: 'attorney@firm.com', name: 'Test Attorney', role: 'attorney' },
    },
  ])
  mockPrisma.client.findUnique.mockResolvedValue({
    id: CLIENT_ID,
    name: 'John Smith',
    contact_email: 'john@example.com',
    contact_phone: '555-1234',
    address: '123 Main St',
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
  })
  mockPrisma.matterClient.findMany.mockResolvedValue([
    {
      matter_id: MATTER_ID,
      client_id: CLIENT_ID,
      client: {
        id: CLIENT_ID,
        name: 'John Smith',
        contact_email: 'john@example.com',
        contact_phone: '555-1234',
        address: '123 Main St',
        created_at: new Date('2024-01-01T00:00:00Z'),
        updated_at: new Date('2024-01-01T00:00:00Z'),
      },
    },
  ])
  mockPrisma.document.findUnique.mockResolvedValue({
    id: DOC_ID,
    matter_id: MATTER_ID,
    file_name: 'contract.pdf',
    file_path: '/docs/contract.pdf',
    file_size: 1024,
    mime_type: 'application/pdf',
    sha256_hash: 'abc123def456',
    status: 'indexed',
    uploaded_by_id: USER_ID,
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
    indexed_at: new Date('2024-01-01T00:00:00Z'),
  })
  mockPrisma.document.findMany.mockResolvedValue([
    {
      id: DOC_ID,
      matter_id: MATTER_ID,
      file_name: 'contract.pdf',
      file_path: '/docs/contract.pdf',
      file_size: 1024,
      mime_type: 'application/pdf',
      sha256_hash: 'abc123def456',
      status: 'indexed',
      uploaded_by_id: USER_ID,
      created_at: new Date('2024-01-01T00:00:00Z'),
      updated_at: new Date('2024-01-01T00:00:00Z'),
      indexed_at: new Date('2024-01-01T00:00:00Z'),
    },
  ])
  mockPrisma.conversation.findUnique.mockResolvedValue({
    id: CONV_ID,
    matter_id: MATTER_ID,
    title: 'Research query',
    created_by_id: USER_ID,
    created_at: new Date('2024-01-01T00:00:00Z'),
    updated_at: new Date('2024-01-01T00:00:00Z'),
    messages: [
      {
        id: MSG_ID,
        conversation_id: CONV_ID,
        role: 'user',
        content: 'What is the status?',
        citations: null,
        created_at: new Date('2024-01-01T00:00:00Z'),
      },
    ],
  })
  mockPrisma.message.create.mockResolvedValue({
    id: MSG_ID,
    conversation_id: CONV_ID,
    role: 'assistant',
    content: 'Here is the answer.',
    citations: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
  })
  mockPrisma.auditLog.create.mockResolvedValue({
    id: 'audit-log-1',
    user_id: USER_ID,
    action: 'document_view',
    resource_type: 'document',
    resource_id: DOC_ID,
    metadata: { fields: ['name'] },
    ip_address: null,
    created_at: new Date('2024-01-01T00:00:00Z'),
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.1 — Scaffold: MCP server starts and lists zero tools
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.1 — MCP Server Scaffold', () => {
  it('createMcpServer() returns an McpServer with a connect() method', () => {
    const server = createMcpServer()
    expect(server).toBeDefined()
    expect(typeof server.connect).toBe('function')
  })

  it('server connects via InMemoryTransport and lists tools/list', async () => {
    const { client, server } = await createTestPair()
    const result = await client.listTools()
    expect(result.tools).toBeDefined()
    expect(Array.isArray(result.tools)).toBe(true)
    await server.close()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.2 — Matter tools: get_matter · list_matters · get_matter_assignments
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.2 — Matter Tools', () => {
  let client: Client
  let server: ReturnType<typeof createMcpServer>

  beforeAll(async () => {
    ;({ client, server } = await createTestPair())
  })

  afterAll(async () => {
    await server.close()
  })

  it('tools/list includes get_matter, list_matters, get_matter_assignments', async () => {
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)
    expect(names).toContain('get_matter')
    expect(names).toContain('list_matters')
    expect(names).toContain('get_matter_assignments')
  })

  it('get_matter returns matter JSON for a valid ID', async () => {
    const result = await client.callTool({ name: 'get_matter', arguments: { id: MATTER_ID } })
    expect(result.isError).toBeFalsy()
    const matter = parseToolText(result.content) as { id: string; title: string; case_number: string }
    expect(matter.id).toBe(MATTER_ID)
    expect(matter.title).toBe('Smith v. Jones')
    expect(matter.case_number).toBe('CASE-2024-001')
    expect(mockPrisma.matter.findUnique).toHaveBeenCalledWith({ where: { id: MATTER_ID } })
  })

  it('get_matter returns isError when matter is not found', async () => {
    mockPrisma.matter.findUnique.mockResolvedValueOnce(null)
    const result = await client.callTool({ name: 'get_matter', arguments: { id: OTHER_MATTER_ID } })
    expect(result.isError).toBe(true)
    const block = result.content[0] as { type: string; text: string }
    expect(block.text).toMatch(/not found/i)
  })

  it('list_matters returns an array of matters', async () => {
    const result = await client.callTool({ name: 'list_matters', arguments: {} })
    expect(result.isError).toBeFalsy()
    const matters = parseToolText(result.content) as unknown[]
    expect(Array.isArray(matters)).toBe(true)
    expect(matters).toHaveLength(1)
    expect((matters[0] as { id: string }).id).toBe(MATTER_ID)
    expect(mockPrisma.matter.findMany).toHaveBeenCalled()
  })

  it('get_matter_assignments returns assignments with user info', async () => {
    const result = await client.callTool({ name: 'get_matter_assignments', arguments: { matter_id: MATTER_ID } })
    expect(result.isError).toBeFalsy()
    const assignments = parseToolText(result.content) as unknown[]
    expect(Array.isArray(assignments)).toBe(true)
    expect(assignments).toHaveLength(1)
    const first = assignments[0] as { matter_id: string; user: { email: string } }
    expect(first.matter_id).toBe(MATTER_ID)
    expect(first.user.email).toBe('attorney@firm.com')
    expect(mockPrisma.matterAssignment.findMany).toHaveBeenCalledWith({
      where: { matter_id: MATTER_ID },
      include: { user: true },
    })
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.3 — Client tools: get_client · list_clients_for_matter
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.3 — Client Tools', () => {
  let client: Client
  let server: ReturnType<typeof createMcpServer>

  beforeAll(async () => {
    ;({ client, server } = await createTestPair())
  })

  afterAll(async () => {
    await server.close()
  })

  it('tools/list includes get_client and list_clients_for_matter', async () => {
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)
    expect(names).toContain('get_client')
    expect(names).toContain('list_clients_for_matter')
  })

  it('get_client returns client JSON for a valid ID', async () => {
    const result = await client.callTool({ name: 'get_client', arguments: { id: CLIENT_ID } })
    expect(result.isError).toBeFalsy()
    const clientData = parseToolText(result.content) as { id: string; name: string; contact_email: string }
    expect(clientData.id).toBe(CLIENT_ID)
    expect(clientData.name).toBe('John Smith')
    expect(clientData.contact_email).toBe('john@example.com')
    expect(mockPrisma.client.findUnique).toHaveBeenCalledWith({ where: { id: CLIENT_ID } })
  })

  it('get_client returns isError when client is not found', async () => {
    mockPrisma.client.findUnique.mockResolvedValueOnce(null)
    const result = await client.callTool({ name: 'get_client', arguments: { id: 'nonexistent-id' } })
    expect(result.isError).toBe(true)
    const block = result.content[0] as { type: string; text: string }
    expect(block.text).toMatch(/not found/i)
  })

  it('list_clients_for_matter returns clients linked to a matter', async () => {
    const result = await client.callTool({ name: 'list_clients_for_matter', arguments: { matter_id: MATTER_ID } })
    expect(result.isError).toBeFalsy()
    const items = parseToolText(result.content) as unknown[]
    expect(Array.isArray(items)).toBe(true)
    expect(items).toHaveLength(1)
    const first = items[0] as { client_id: string; client: { name: string } }
    expect(first.client_id).toBe(CLIENT_ID)
    expect(first.client.name).toBe('John Smith')
    expect(mockPrisma.matterClient.findMany).toHaveBeenCalledWith({
      where: { matter_id: MATTER_ID },
      include: { client: true },
    })
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.4 — Document tools: list_documents_for_matter · get_document
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.4 — Document Tools', () => {
  let client: Client
  let server: ReturnType<typeof createMcpServer>

  beforeAll(async () => {
    ;({ client, server } = await createTestPair())
  })

  afterAll(async () => {
    await server.close()
  })

  it('tools/list includes list_documents_for_matter and get_document', async () => {
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)
    expect(names).toContain('list_documents_for_matter')
    expect(names).toContain('get_document')
  })

  it('list_documents_for_matter returns documents for a matter', async () => {
    const result = await client.callTool({ name: 'list_documents_for_matter', arguments: { matter_id: MATTER_ID } })
    expect(result.isError).toBeFalsy()
    const docs = parseToolText(result.content) as unknown[]
    expect(Array.isArray(docs)).toBe(true)
    expect(docs).toHaveLength(1)
    const doc = docs[0] as { id: string; file_name: string; status: string }
    expect(doc.id).toBe(DOC_ID)
    expect(doc.file_name).toBe('contract.pdf')
    expect(doc.status).toBe('indexed')
    expect(mockPrisma.document.findMany).toHaveBeenCalledWith({ where: { matter_id: MATTER_ID } })
  })

  it('get_document returns document metadata for a valid ID', async () => {
    const result = await client.callTool({ name: 'get_document', arguments: { id: DOC_ID } })
    expect(result.isError).toBeFalsy()
    const doc = parseToolText(result.content) as { id: string; file_name: string; sha256_hash: string }
    expect(doc.id).toBe(DOC_ID)
    expect(doc.file_name).toBe('contract.pdf')
    expect(doc.sha256_hash).toBe('abc123def456')
    expect(mockPrisma.document.findUnique).toHaveBeenCalledWith({ where: { id: DOC_ID } })
  })

  it('get_document returns isError when document is not found', async () => {
    mockPrisma.document.findUnique.mockResolvedValueOnce(null)
    const result = await client.callTool({ name: 'get_document', arguments: { id: 'nonexistent-id' } })
    expect(result.isError).toBe(true)
    const block = result.content[0] as { type: string; text: string }
    expect(block.text).toMatch(/not found/i)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.5 — Conversation tools: get_conversation · save_message
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.5 — Conversation Tools', () => {
  let client: Client
  let server: ReturnType<typeof createMcpServer>

  beforeAll(async () => {
    ;({ client, server } = await createTestPair())
  })

  afterAll(async () => {
    await server.close()
  })

  it('tools/list includes get_conversation and save_message', async () => {
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)
    expect(names).toContain('get_conversation')
    expect(names).toContain('save_message')
  })

  it('get_conversation returns conversation with messages', async () => {
    const result = await client.callTool({ name: 'get_conversation', arguments: { id: CONV_ID } })
    expect(result.isError).toBeFalsy()
    const conv = parseToolText(result.content) as { id: string; title: string; messages: unknown[] }
    expect(conv.id).toBe(CONV_ID)
    expect(conv.title).toBe('Research query')
    expect(Array.isArray(conv.messages)).toBe(true)
    expect(conv.messages).toHaveLength(1)
    expect(mockPrisma.conversation.findUnique).toHaveBeenCalledWith({
      where: { id: CONV_ID },
      include: { messages: true },
    })
  })

  it('get_conversation returns isError when conversation is not found', async () => {
    mockPrisma.conversation.findUnique.mockResolvedValueOnce(null)
    const result = await client.callTool({ name: 'get_conversation', arguments: { id: 'nonexistent-id' } })
    expect(result.isError).toBe(true)
    const block = result.content[0] as { type: string; text: string }
    expect(block.text).toMatch(/not found/i)
  })

  it('save_message creates a message and returns the new record', async () => {
    const result = await client.callTool({
      name: 'save_message',
      arguments: {
        conversation_id: CONV_ID,
        role: 'assistant',
        content: 'Here is the answer.',
      },
    })
    expect(result.isError).toBeFalsy()
    const msg = parseToolText(result.content) as { id: string; role: string; content: string }
    expect(msg.id).toBe(MSG_ID)
    expect(msg.role).toBe('assistant')
    expect(msg.content).toBe('Here is the answer.')
    expect(mockPrisma.message.create).toHaveBeenCalledWith({
      data: { conversation_id: CONV_ID, role: 'assistant', content: 'Here is the answer.' },
    })
  })

  it('save_message accepts optional citations JSONB', async () => {
    const citations = [{ doc_id: DOC_ID, chunk_id: 'chunk-1', text_snippet: 'relevant text', page: 3 }]
    const result = await client.callTool({
      name: 'save_message',
      arguments: {
        conversation_id: CONV_ID,
        role: 'assistant',
        content: 'Cited answer.',
        citations: JSON.stringify(citations),
      },
    })
    expect(result.isError).toBeFalsy()
    expect(mockPrisma.message.create).toHaveBeenCalledWith({
      data: expect.objectContaining({ citations }),
    })
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.6 — Audit tool: log_audit_event
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.6 — Audit Tool', () => {
  let client: Client
  let server: ReturnType<typeof createMcpServer>

  beforeAll(async () => {
    ;({ client, server } = await createTestPair())
  })

  afterAll(async () => {
    await server.close()
  })

  it('tools/list includes log_audit_event', async () => {
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)
    expect(names).toContain('log_audit_event')
  })

  it('log_audit_event creates an audit log row and returns the record', async () => {
    const result = await client.callTool({
      name: 'log_audit_event',
      arguments: {
        user_id: USER_ID,
        action: 'document_view',
        resource_type: 'document',
        resource_id: DOC_ID,
      },
    })
    expect(result.isError).toBeFalsy()
    const log = parseToolText(result.content) as { id: string; action: string; resource_type: string }
    expect(log.id).toBe('audit-log-1')
    expect(log.action).toBe('document_view')
    expect(log.resource_type).toBe('document')
    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        user_id: USER_ID,
        action: 'document_view',
        resource_type: 'document',
        resource_id: DOC_ID,
      }),
    })
  })

  it('log_audit_event accepts optional metadata and ip_address', async () => {
    const result = await client.callTool({
      name: 'log_audit_event',
      arguments: {
        user_id: USER_ID,
        action: 'pii_access',
        resource_type: 'message',
        resource_id: MSG_ID,
        metadata: JSON.stringify({ fields: ['name', 'ssn'] }),
        ip_address: '192.168.1.100',
      },
    })
    expect(result.isError).toBeFalsy()
    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        metadata: { fields: ['name', 'ssn'] },
        ip_address: '192.168.1.100',
      }),
    })
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Task 2.7 — Integration: all tools are registered and callable
// ─────────────────────────────────────────────────────────────────────────────

describe('Task 2.7 — Full Integration: all MCP tools registered', () => {
  it('tools/list returns all 10 expected tools', async () => {
    const { client, server } = await createTestPair()
    const { tools } = await client.listTools()
    const names = tools.map((t) => t.name)

    const expected = [
      'get_matter',
      'list_matters',
      'get_matter_assignments',
      'get_client',
      'list_clients_for_matter',
      'list_documents_for_matter',
      'get_document',
      'get_conversation',
      'save_message',
      'log_audit_event',
    ]

    for (const name of expected) {
      expect(names, `expected tool "${name}" to be registered`).toContain(name)
    }
    expect(tools).toHaveLength(expected.length)

    await server.close()
  })

  it('each tool has a description and inputSchema', async () => {
    const { client, server } = await createTestPair()
    const { tools } = await client.listTools()

    for (const tool of tools) {
      expect(tool.description, `${tool.name} should have a description`).toBeTruthy()
      expect(tool.inputSchema, `${tool.name} should have an inputSchema`).toBeDefined()
    }

    await server.close()
  })
})
