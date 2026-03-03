/**
 * Phase 9 — Task 9.12: Audit log completeness test
 *
 * After a scripted workflow, the audit_logs table has entries for every
 * auditable action. Verifies:
 *   - PII access events are logged (PII_ACCESS)
 *   - Document view events are logged (VIEW_DOCUMENT)
 *   - Search/query events are logged (CHAT_QUERY / SEARCH)
 *   - Login events are logged (LOGIN)
 *   - All entries have required fields: user_id, action, resource_type, resource_id, created_at
 *   - Metadata carries audit-specific context (matter_id, pii_fields, etc.)
 *   - Multiple events accumulate — none are dropped
 *   - Sensitive actions without a matter_id context are still logged
 *
 * All Prisma calls are mocked — no real database required.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logEvent } from '../src/services/audit'

// ── Prisma mock ───────────────────────────────────────────────────────────────

let auditLogStore: unknown[] = []

const { mockPrisma } = vi.hoisted(() => {
  const store: unknown[] = []

  return {
    mockPrisma: {
      auditLog: {
        create: vi.fn().mockImplementation(async ({ data }: { data: unknown }) => {
          const entry = {
            ...(data as object),
            id: `audit-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            created_at: new Date(),
          }
          store.push(entry)
          return entry
        }),
        findMany: vi.fn().mockImplementation(async () => store),
      },
      _store: store,
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(function () {
    return mockPrisma
  }),
}))

beforeEach(() => {
  vi.clearAllMocks()
  auditLogStore = []
  // Reset mock to accumulate into our controlled store
  mockPrisma.auditLog.create.mockImplementation(async ({ data }: { data: unknown }) => {
    const entry = {
      ...(data as object),
      id: `audit-${auditLogStore.length + 1}`,
      created_at: new Date(),
    }
    auditLogStore.push(entry)
    return entry
  })
  mockPrisma.auditLog.findMany.mockImplementation(async () => auditLogStore)
})

// ── Required fields contract ──────────────────────────────────────────────────

describe('Audit log completeness — required field contract (Task 9.12)', () => {
  it('every audit entry contains user_id', async () => {
    const userId = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    await logEvent({
      userId,
      action: 'LOGIN',
      resourceType: 'user',
      resourceId: userId,
    })
    const entry = auditLogStore[0] as Record<string, unknown>
    expect(entry.user_id).toBe(userId)
    expect(typeof entry.user_id).toBe('string')
    expect(entry.user_id).not.toBe('')
  })

  it('every audit entry contains action', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'doc-001',
    })
    const entry = auditLogStore[0] as Record<string, unknown>
    expect(typeof entry.action).toBe('string')
    expect(entry.action).toBe('VIEW_DOCUMENT')
  })

  it('every audit entry contains resource_type and resource_id', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
    })
    const entry = auditLogStore[0] as Record<string, unknown>
    expect(entry.resource_type).toBe('document')
    expect(entry.resource_id).toBe('doc-uuid-001')
  })

  it('entry has a created_at timestamp', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'CHAT_QUERY',
      resourceType: 'conversation',
      resourceId: 'conv-001',
    })
    const entry = auditLogStore[0] as Record<string, unknown>
    expect(entry.created_at).toBeDefined()
    expect(entry.created_at instanceof Date || typeof entry.created_at === 'string').toBe(true)
  })
})

// ── Scripted workflow — all auditable actions are logged ──────────────────────

describe('Scripted workflow completeness (Task 9.12)', () => {
  const USER_ID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
  const MATTER_ID = 'matter-uuid-001'
  const DOC_ID = 'doc-uuid-001'
  const CONV_ID = 'conv-uuid-001'

  async function runScriptedWorkflow(): Promise<void> {
    // 1. User logs in
    await logEvent({ userId: USER_ID, action: 'LOGIN', resourceType: 'user', resourceId: USER_ID })

    // 2. User accesses a document (VIEW)
    await logEvent({
      userId: USER_ID,
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: DOC_ID,
      metadata: { matter_id: MATTER_ID, file_name: 'contract.pdf' },
    })

    // 3. Document contains PII — access is logged
    await logEvent({
      userId: USER_ID,
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: DOC_ID,
      metadata: { pii_fields: ['PERSON', 'US_SSN'], matter_id: MATTER_ID, redacted_before_llm: true },
    })

    // 4. User runs a chat query (SEARCH / retrieval)
    await logEvent({
      userId: USER_ID,
      action: 'CHAT_QUERY',
      resourceType: 'conversation',
      resourceId: CONV_ID,
      metadata: { matter_id: MATTER_ID, query_length: 55, has_pii: false, intent: 'retrieval' },
    })

    // 5. Search returns results referencing another document — log document view
    await logEvent({
      userId: USER_ID,
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'doc-uuid-002',
      metadata: { matter_id: MATTER_ID, file_name: 'brief.pdf', chunk_id: 'doc-uuid-002_0' },
    })

    // 6. User logs out
    await logEvent({ userId: USER_ID, action: 'LOGOUT', resourceType: 'user', resourceId: USER_ID })
  }

  it('all 6 workflow steps produce an audit log entry', async () => {
    await runScriptedWorkflow()
    expect(auditLogStore).toHaveLength(6)
  })

  it('LOGIN event is present in audit log', async () => {
    await runScriptedWorkflow()
    const loginEntry = auditLogStore.find(
      (e) => (e as Record<string, unknown>).action === 'LOGIN',
    ) as Record<string, unknown> | undefined
    expect(loginEntry).toBeDefined()
    expect(loginEntry?.user_id).toBe(USER_ID)
  })

  it('VIEW_DOCUMENT events are present (at least one)', async () => {
    await runScriptedWorkflow()
    const viewEvents = auditLogStore.filter(
      (e) => (e as Record<string, unknown>).action === 'VIEW_DOCUMENT',
    )
    expect(viewEvents.length).toBeGreaterThanOrEqual(1)
  })

  it('PII_ACCESS event is logged with pii_fields in metadata', async () => {
    await runScriptedWorkflow()
    const piiEntry = auditLogStore.find(
      (e) => (e as Record<string, unknown>).action === 'PII_ACCESS',
    ) as Record<string, unknown> | undefined
    expect(piiEntry).toBeDefined()
    const meta = piiEntry?.metadata as Record<string, unknown>
    expect(meta?.pii_fields).toContain('PERSON')
    expect(meta?.pii_fields).toContain('US_SSN')
  })

  it('CHAT_QUERY event is logged with matter_id in metadata', async () => {
    await runScriptedWorkflow()
    const chatEntry = auditLogStore.find(
      (e) => (e as Record<string, unknown>).action === 'CHAT_QUERY',
    ) as Record<string, unknown> | undefined
    expect(chatEntry).toBeDefined()
    const meta = chatEntry?.metadata as Record<string, unknown>
    expect(meta?.matter_id).toBe(MATTER_ID)
  })

  it('LOGOUT event is present in audit log', async () => {
    await runScriptedWorkflow()
    const logoutEntry = auditLogStore.find(
      (e) => (e as Record<string, unknown>).action === 'LOGOUT',
    ) as Record<string, unknown> | undefined
    expect(logoutEntry).toBeDefined()
  })

  it('no audit entries are dropped — all createMany calls propagate', async () => {
    await runScriptedWorkflow()
    // prisma.auditLog.create should be called exactly once per step
    expect(mockPrisma.auditLog.create).toHaveBeenCalledTimes(6)
  })
})

// ── Audit log is append-only ──────────────────────────────────────────────────

describe('Audit log append-only invariant (Task 9.12)', () => {
  it('logEvent only calls prisma.create, never update', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-001',
      metadata: { pii_fields: ['PERSON'] },
    })
    expect(mockPrisma.auditLog.create).toHaveBeenCalledTimes(1)
    // Verify no update method is present on mock (create-only pattern)
    expect((mockPrisma.auditLog as Record<string, unknown>).update).toBeUndefined()
  })

  it('consecutive logEvent calls each produce a separate DB write', async () => {
    const actions = ['PII_ACCESS', 'VIEW_DOCUMENT', 'CHAT_QUERY'] as const
    for (const action of actions) {
      await logEvent({
        userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        action,
        resourceType: action === 'CHAT_QUERY' ? 'conversation' : 'document',
        resourceId: `resource-${action}`,
      })
    }
    expect(mockPrisma.auditLog.create).toHaveBeenCalledTimes(actions.length)
    expect(auditLogStore).toHaveLength(actions.length)
  })
})

// ── Edge cases ────────────────────────────────────────────────────────────────

describe('Audit log edge cases (Task 9.12)', () => {
  it('logs an event without metadata (metadata is optional)', async () => {
    await expect(
      logEvent({
        userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        action: 'LOGIN',
        resourceType: 'user',
        resourceId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      }),
    ).resolves.not.toThrow()
    expect(auditLogStore).toHaveLength(1)
  })

  it('logs an event with ip_address', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'LOGIN',
      resourceType: 'user',
      resourceId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      ipAddress: '10.0.0.5',
    })
    const entry = auditLogStore[0] as Record<string, unknown>
    expect(entry.ip_address).toBe('10.0.0.5')
  })

  it('supports all required action types enumerated in compliance requirements', async () => {
    const complianceActions = [
      'PII_ACCESS',
      'VIEW_DOCUMENT',
      'CHAT_QUERY',
      'LOGIN',
      'LOGOUT',
      'SEARCH',
      'DOCUMENT_UPLOAD',
    ]

    for (const action of complianceActions) {
      await logEvent({
        userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        action,
        resourceType: 'document',
        resourceId: 'res-001',
      })
    }

    expect(auditLogStore).toHaveLength(complianceActions.length)
    const loggedActions = auditLogStore.map((e) => (e as Record<string, unknown>).action)
    for (const action of complianceActions) {
      expect(loggedActions).toContain(action)
    }
  })
})
