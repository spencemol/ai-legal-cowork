/**
 * Phase 2, Task 2.3 — MCP tools for clients
 *
 * Registers: get_client · list_clients_for_matter
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { prisma } from '../../db'

export function registerClientTools(server: McpServer): void {
  // ── get_client ────────────────────────────────────────────────────────────
  server.registerTool(
    'get_client',
    {
      description: 'Get a client by ID. Returns client contact information including name, email, phone, and address.',
      inputSchema: {
        id: z.string().describe('The UUID of the client to retrieve'),
      },
    },
    async ({ id }) => {
      const client = await prisma.client.findUnique({ where: { id } })
      if (!client) {
        return {
          content: [{ type: 'text', text: `Client not found: ${id}` }],
          isError: true,
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify(client) }] }
    },
  )

  // ── list_clients_for_matter ───────────────────────────────────────────────
  server.registerTool(
    'list_clients_for_matter',
    {
      description: 'List all clients linked to a matter, including their role (plaintiff, defendant, etc.) and contact details.',
      inputSchema: {
        matter_id: z.string().describe('The UUID of the matter'),
      },
    },
    async ({ matter_id }) => {
      const links = await prisma.matterClient.findMany({
        where: { matter_id },
        include: { client: true },
      })
      return { content: [{ type: 'text', text: JSON.stringify(links) }] }
    },
  )
}
