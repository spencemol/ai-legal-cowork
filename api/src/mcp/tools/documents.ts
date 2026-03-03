/**
 * Phase 2, Task 2.4 — MCP tools for the document registry
 *
 * Registers: list_documents_for_matter · get_document
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { prisma } from '../../db'

export function registerDocumentTools(server: McpServer): void {
  // ── list_documents_for_matter ─────────────────────────────────────────────
  server.registerTool(
    'list_documents_for_matter',
    {
      description:
        'List all documents registered for a matter. Returns file metadata including name, path, MIME type, hash, and ingestion status.',
      inputSchema: {
        matter_id: z.string().describe('The UUID of the matter'),
      },
    },
    async ({ matter_id }) => {
      const documents = await prisma.document.findMany({ where: { matter_id } })
      return { content: [{ type: 'text', text: JSON.stringify(documents) }] }
    },
  )

  // ── get_document ──────────────────────────────────────────────────────────
  server.registerTool(
    'get_document',
    {
      description: 'Get a document record by ID. Returns full document metadata including SHA-256 hash and ingestion status.',
      inputSchema: {
        id: z.string().describe('The UUID of the document to retrieve'),
      },
    },
    async ({ id }) => {
      const document = await prisma.document.findUnique({ where: { id } })
      if (!document) {
        return {
          content: [{ type: 'text', text: `Document not found: ${id}` }],
          isError: true,
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify(document) }] }
    },
  )
}
