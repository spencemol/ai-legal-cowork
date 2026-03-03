/**
 * Phase 2, Task 2.2 — MCP tools for matters
 *
 * Registers: get_matter · list_matters · get_matter_assignments
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { prisma } from '../../db'

export function registerMatterTools(server: McpServer): void {
  // ── get_matter ────────────────────────────────────────────────────────────
  server.registerTool(
    'get_matter',
    {
      description: 'Get a legal matter by ID. Returns matter metadata including title, case number, status, and timestamps.',
      inputSchema: {
        id: z.string().describe('The UUID of the matter to retrieve'),
      },
    },
    async ({ id }) => {
      const matter = await prisma.matter.findUnique({ where: { id } })
      if (!matter) {
        return {
          content: [{ type: 'text', text: `Matter not found: ${id}` }],
          isError: true,
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify(matter) }] }
    },
  )

  // ── list_matters ──────────────────────────────────────────────────────────
  server.registerTool(
    'list_matters',
    {
      description: 'List all legal matters. Returns an array of matter records.',
      inputSchema: {},
    },
    async () => {
      const matters = await prisma.matter.findMany()
      return { content: [{ type: 'text', text: JSON.stringify(matters) }] }
    },
  )

  // ── get_matter_assignments ────────────────────────────────────────────────
  server.registerTool(
    'get_matter_assignments',
    {
      description:
        'Get all user assignments for a matter, including user details and access levels (full, restricted, read_only).',
      inputSchema: {
        matter_id: z.string().describe('The UUID of the matter'),
      },
    },
    async ({ matter_id }) => {
      const assignments = await prisma.matterAssignment.findMany({
        where: { matter_id },
        include: { user: true },
      })
      return { content: [{ type: 'text', text: JSON.stringify(assignments) }] }
    },
  )
}
