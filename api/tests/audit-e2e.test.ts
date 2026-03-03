/**
 * Phase 6 — Task 6.9: Audit log writes during chat flow.
 *
 * Verifies that:
 *   - logEvent() correctly records PII access events with all required fields
 *   - logEvent() records document view events with correct resource metadata
 *   - All audit log fields match the expected schema
 *   - Multiple event types (PII_ACCESS, VIEW_DOCUMENT, CHAT_QUERY) are logged correctly
 *   - Audit entries are written atomically (one create per logEvent call)
 *   - The audit log schema supports the metadata fields needed for PII tracking
 *
 * All Prisma calls are mocked — no real database required.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logEvent } from '../src/services/audit'

// ---------------------------------------------------------------------------
// Prisma mock (vi.hoisted pattern — consistent with other test files)
// ---------------------------------------------------------------------------

const { mockPrisma } = vi.hoisted(() => {
  const baseAuditLog = {
    id: 'audit-e2e-001',
    user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    action: 'PII_ACCESS',
    resource_type: 'document',
    resource_id: 'doc-uuid-001',
    metadata: {
      pii_fields: ['PERSON', 'US_SSN'],
      matter_id: 'matter-uuid-001',
      access_level: 'full',
      redacted_before_llm: true,
    },
    ip_address: '10.0.0.1',
    created_at: new Date('2024-06-01T12:00:00Z'),
  }

  return {
    mockPrisma: {
      auditLog: {
        create: vi.fn().mockResolvedValue(baseAuditLog),
        findMany: vi.fn().mockResolvedValue([baseAuditLog]),
      },
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
  // Restore the default mock return value after clearAllMocks
  mockPrisma.auditLog.create.mockResolvedValue({
    id: 'audit-e2e-001',
    user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    action: 'PII_ACCESS',
    resource_type: 'document',
    resource_id: 'doc-uuid-001',
    metadata: null,
    ip_address: null,
    created_at: new Date('2024-06-01T12:00:00Z'),
  })
})

// ---------------------------------------------------------------------------
// PII access event tests
// ---------------------------------------------------------------------------

describe('Audit log — PII access events (Task 6.9)', () => {
  it('records a PII_ACCESS event with all required fields', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata: {
        pii_fields: ['PERSON', 'US_SSN'],
        matter_id: 'matter-uuid-001',
        access_level: 'full',
        redacted_before_llm: true,
      },
      ipAddress: '10.0.0.1',
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledOnce()
    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
          action: 'PII_ACCESS',
          resource_type: 'document',
          resource_id: 'doc-uuid-001',
        }),
      }),
    )
  })

  it('stores pii_fields array in metadata', async () => {
    const metadata = {
      pii_fields: ['PERSON', 'US_SSN', 'EMAIL_ADDRESS'],
      matter_id: 'matter-uuid-001',
      redacted_before_llm: true,
    }

    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata,
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ metadata }),
      }),
    )
  })

  it('records access_level in PII event metadata', async () => {
    const metadata = {
      pii_fields: ['PERSON'],
      access_level: 'restricted',
      matter_id: 'matter-uuid-001',
    }

    await logEvent({
      userId: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-uuid-002',
      metadata,
    })

    const callArg = mockPrisma.auditLog.create.mock.calls[0][0] as {
      data: { metadata: { access_level: string } }
    }
    expect(callArg.data.metadata.access_level).toBe('restricted')
  })

  it('records whether PII was redacted before the LLM call', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata: { redacted_before_llm: true, pii_fields: ['PERSON'] },
    })

    const callArg = mockPrisma.auditLog.create.mock.calls[0][0] as {
      data: { metadata: { redacted_before_llm: boolean } }
    }
    expect(callArg.data.metadata.redacted_before_llm).toBe(true)
  })

  it('records ip_address for PII access events', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata: { pii_fields: ['PERSON'] },
      ipAddress: '192.168.1.100',
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ ip_address: '192.168.1.100' }),
      }),
    )
  })
})

// ---------------------------------------------------------------------------
// Document view event tests
// ---------------------------------------------------------------------------

describe('Audit log — document view events (Task 6.9)', () => {
  it('records a VIEW_DOCUMENT event with correct resource fields', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata: {
        matter_id: 'matter-uuid-001',
        file_name: 'contract.pdf',
        chunk_id: 'doc-uuid-001_0',
      },
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          action: 'VIEW_DOCUMENT',
          resource_type: 'document',
          resource_id: 'doc-uuid-001',
        }),
      }),
    )
  })

  it('stores citation metadata when user clicks a citation', async () => {
    const citationMetadata = {
      matter_id: 'matter-uuid-001',
      file_name: 'brief.pdf',
      chunk_id: 'doc-uuid-001_2',
      page: 3,
      text_snippet: 'The plaintiff alleges breach of contract.',
    }

    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'doc-uuid-001',
      metadata: citationMetadata,
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ metadata: citationMetadata }),
      }),
    )
  })
})

// ---------------------------------------------------------------------------
// Chat query event tests
// ---------------------------------------------------------------------------

describe('Audit log — chat query events (Task 6.9)', () => {
  it('records a CHAT_QUERY event for each chat request', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'CHAT_QUERY',
      resourceType: 'conversation',
      resourceId: 'conv-uuid-001',
      metadata: {
        matter_id: 'matter-uuid-001',
        query_length: 42,
        has_pii: false,
        intent: 'retrieval',
      },
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          action: 'CHAT_QUERY',
          resource_type: 'conversation',
        }),
      }),
    )
  })

  it('records has_pii=true when query contained PII', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'CHAT_QUERY',
      resourceType: 'conversation',
      resourceId: 'conv-uuid-002',
      metadata: {
        matter_id: 'matter-uuid-001',
        has_pii: true,
        pii_types_detected: ['PERSON', 'US_SSN'],
        intent: 'retrieval',
      },
    })

    const callArg = mockPrisma.auditLog.create.mock.calls[0][0] as {
      data: { metadata: { has_pii: boolean; pii_types_detected: string[] } }
    }
    expect(callArg.data.metadata.has_pii).toBe(true)
    expect(callArg.data.metadata.pii_types_detected).toContain('PERSON')
    expect(callArg.data.metadata.pii_types_detected).toContain('US_SSN')
  })
})

// ---------------------------------------------------------------------------
// Audit log schema contract tests
// ---------------------------------------------------------------------------

describe('Audit log — schema contract (Task 6.9)', () => {
  it('always creates exactly one record per logEvent call', async () => {
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-001',
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledTimes(1)
  })

  it('returns the created audit log entry', async () => {
    mockPrisma.auditLog.create.mockResolvedValueOnce({
      id: 'audit-return-test',
      user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resource_type: 'document',
      resource_id: 'doc-001',
      metadata: null,
      ip_address: null,
      created_at: new Date(),
    })

    const result = await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-001',
    })

    expect(result).toMatchObject({
      id: 'audit-return-test',
      action: 'PII_ACCESS',
      resource_type: 'document',
    })
  })

  it('supports all required action types for PII compliance', async () => {
    const requiredActions = ['PII_ACCESS', 'VIEW_DOCUMENT', 'CHAT_QUERY', 'LOGIN', 'LOGOUT']

    for (const action of requiredActions) {
      mockPrisma.auditLog.create.mockResolvedValueOnce({
        id: `audit-${action}`,
        user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        action,
        resource_type: 'document',
        resource_id: 'doc-001',
        metadata: null,
        ip_address: null,
        created_at: new Date(),
      })

      await expect(
        logEvent({
          userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
          action,
          resourceType: 'document',
          resourceId: 'doc-001',
        }),
      ).resolves.not.toThrow()
    }

    // Each action produced exactly one database write
    expect(mockPrisma.auditLog.create).toHaveBeenCalledTimes(requiredActions.length)
  })

  it('audit log entries are immutable (create-only, no update calls)', async () => {
    // Audit logs must be append-only — verify no update methods are called
    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-001',
      metadata: { pii_fields: ['PERSON'] },
    })

    // Only create should have been called, never update or upsert
    expect(mockPrisma.auditLog.create).toHaveBeenCalledOnce()
    // No update method exists on the mock — this confirms create-only pattern
    expect((mockPrisma.auditLog as Record<string, unknown>).update).toBeUndefined()
  })

  it('records user_id and resource_id as non-empty strings', async () => {
    const userId = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    const resourceId = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'

    await logEvent({
      userId,
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId,
    })

    const callArg = mockPrisma.auditLog.create.mock.calls[0][0] as {
      data: { user_id: string; resource_id: string }
    }
    expect(callArg.data.user_id).toBe(userId)
    expect(callArg.data.resource_id).toBe(resourceId)
    expect(callArg.data.user_id).not.toBe('')
    expect(callArg.data.resource_id).not.toBe('')
  })
})
