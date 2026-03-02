/**
 * Phase 1 — Audit Log Service Tests (Tasks 1.17, 1.18)
 *
 * ALL TESTS EXPECTED TO FAIL until the audit service is implemented.
 *   - Dynamic import of '../src/services/audit' will throw "Cannot find module"
 *     until task 1.18 creates src/services/audit.ts
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'

const { mockPrisma } = vi.hoisted(() => {
  return {
    mockPrisma: {
      auditLog: {
        create: vi.fn().mockResolvedValue({
          id: 'audit-log-1',
          user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
          action: 'VIEW_DOCUMENT',
          resource_type: 'document',
          resource_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
          metadata: { fileName: 'contract.pdf' },
          created_at: new Date('2024-01-01T00:00:00Z'),
        }),
        findMany: vi.fn().mockResolvedValue([]),
      },
    },
  }
})

vi.mock('@prisma/client', () => ({
  PrismaClient: vi.fn(() => mockPrisma),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── Task 1.18 — Audit log service unit tests ─────────────────────────────────

describe('logEvent (src/services/audit.ts)', () => {
  it('calls prisma.auditLog.create with correct shape', async () => {
    // This dynamic import will fail until src/services/audit.ts is created (task 1.18)
    const { logEvent } = await import('../src/services/audit')

    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      metadata: { fileName: 'contract.pdf' },
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledOnce()
    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          user_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
          action: 'VIEW_DOCUMENT',
          resource_type: 'document',
          resource_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
        }),
      }),
    )
  })

  it('stores metadata as JSON', async () => {
    const { logEvent } = await import('../src/services/audit')
    const metadata = { fileName: 'brief.pdf', piiAccessed: true, fields: ['name', 'ssn'] }

    await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'PII_ACCESS',
      resourceType: 'document',
      resourceId: 'doc-123',
      metadata,
    })

    expect(mockPrisma.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ metadata }),
      }),
    )
  })

  it('allows null metadata (optional field)', async () => {
    const { logEvent } = await import('../src/services/audit')

    await expect(
      logEvent({
        userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        action: 'LOGIN',
        resourceType: 'user',
        resourceId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      }),
    ).resolves.not.toThrow()
  })

  it('returns the created audit log entry', async () => {
    const { logEvent } = await import('../src/services/audit')

    const result = await logEvent({
      userId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      action: 'VIEW_DOCUMENT',
      resourceType: 'document',
      resourceId: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    })

    expect(result).toMatchObject({
      action: 'VIEW_DOCUMENT',
      resource_type: 'document',
    })
  })
})

beforeAll(() => {
  // Reset module cache so each test gets a fresh import
  vi.resetModules()
})
