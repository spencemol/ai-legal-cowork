/**
 * Phase 2, Task 2.5 — MCP tools for conversations
 *
 * Registers: get_conversation · save_message
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { prisma } from '../../db'

export function registerConversationTools(server: McpServer): void {
  // ── get_conversation ──────────────────────────────────────────────────────
  server.registerTool(
    'get_conversation',
    {
      description: 'Get a conversation by ID, including its full message history and any inline citations.',
      inputSchema: {
        id: z.string().describe('The UUID of the conversation to retrieve'),
      },
    },
    async ({ id }) => {
      const conversation = await prisma.conversation.findUnique({
        where: { id },
        include: { messages: true },
      })
      if (!conversation) {
        return {
          content: [{ type: 'text', text: `Conversation not found: ${id}` }],
          isError: true,
        }
      }
      return { content: [{ type: 'text', text: JSON.stringify(conversation) }] }
    },
  )

  // ── save_message ──────────────────────────────────────────────────────────
  server.registerTool(
    'save_message',
    {
      description:
        'Persist a new message to a conversation. Citations are optional and must be passed as a JSON string when present.',
      inputSchema: {
        conversation_id: z.string().describe('The UUID of the conversation'),
        role: z.enum(['user', 'assistant']).describe('The message author role'),
        content: z.string().describe('The message text content'),
        citations: z
          .string()
          .optional()
          .describe('Optional JSON string of citation objects [{doc_id, chunk_id, text_snippet, page}]'),
      },
    },
    async ({ conversation_id, role, content, citations }) => {
      const data: {
        conversation_id: string
        role: 'user' | 'assistant'
        content: string
        citations?: unknown
      } = { conversation_id, role, content }

      if (citations !== undefined) {
        data.citations = JSON.parse(citations) as unknown
      }

      const message = await prisma.message.create({ data })
      return { content: [{ type: 'text', text: JSON.stringify(message) }] }
    },
  )
}
