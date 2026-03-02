import type { AuditLog } from '@prisma/client'
import { prisma } from '../db'

interface LogEventParams {
  userId: string
  action: string
  resourceType: string
  resourceId: string
  metadata?: Record<string, unknown>
}

export async function logEvent(params: LogEventParams): Promise<AuditLog> {
  return prisma.auditLog.create({
    data: {
      user_id: params.userId,
      action: params.action,
      resource_type: params.resourceType,
      resource_id: params.resourceId,
      metadata: params.metadata,
    },
  })
}
