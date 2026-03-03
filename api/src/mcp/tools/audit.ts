/**
 * Phase 2, Task 2.6 — MCP tool for audit logging
 *
 * Registers: log_audit_event
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { logEvent } from '../../services/audit'

export function registerAuditTools(server: McpServer): void {
  // ── log_audit_event ───────────────────────────────────────────────────────
  server.registerTool(
    'log_audit_event',
    {
      description:
        'Record an auditable action to the audit log. Used by the agent backend to log PII accesses, document views, and searches for compliance.',
      inputSchema: {
        user_id: z.string().describe('The UUID of the user performing the action'),
        action: z
          .string()
          .describe('The action identifier, e.g. "pii_access", "document_view", "search"'),
        resource_type: z.string().describe('The type of resource acted upon, e.g. "document", "message"'),
        resource_id: z.string().describe('The UUID of the resource acted upon'),
        metadata: z
          .string()
          .optional()
          .describe('Optional JSON string of additional audit metadata, e.g. {"fields":["ssn","name"]}'),
        ip_address: z.string().optional().describe('Optional IP address of the requester'),
      },
    },
    async ({ user_id, action, resource_type, resource_id, metadata, ip_address }) => {
      const auditLog = await logEvent({
        userId: user_id,
        action,
        resourceType: resource_type,
        resourceId: resource_id,
        metadata: metadata !== undefined ? (JSON.parse(metadata) as Record<string, unknown>) : undefined,
        ipAddress: ip_address,
      })
      return { content: [{ type: 'text', text: JSON.stringify(auditLog) }] }
    },
  )
}
