import type { AuditLog, Prisma } from '@prisma/client'
import { prisma } from '../db'

interface LogEventParams {
  userId: string
  action: string
  resourceType: string
  resourceId: string
  metadata?: Prisma.InputJsonValue
  ipAddress?: string
}

export async function logEvent(params: LogEventParams): Promise<AuditLog> {
  return prisma.auditLog.create({
    data: {
      user_id: params.userId,
      action: params.action,
      resource_type: params.resourceType,
      resource_id: params.resourceId,
      metadata: params.metadata,
      ...(params.ipAddress !== undefined && { ip_address: params.ipAddress }),
    },
  })
}
