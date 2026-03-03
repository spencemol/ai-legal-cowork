/**
 * Phase 2, Task 2.1 — MCP server factory
 *
 * createMcpServer() returns a fully configured McpServer instance with all
 * Phase 2 tools registered. The caller is responsible for connecting it to
 * a transport (InMemoryTransport for tests, StreamableHTTP for production).
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp'
import { registerMatterTools } from './tools/matters'
import { registerClientTools } from './tools/clients'
import { registerDocumentTools } from './tools/documents'
import { registerConversationTools } from './tools/conversations'
import { registerAuditTools } from './tools/audit'

export function createMcpServer(): McpServer {
  const server = new McpServer(
    { name: 'legal-ai-mcp', version: '1.0.0' },
    {
      capabilities: { tools: {} },
      instructions:
        'Legal AI MCP server exposing matter, client, document, conversation, and audit log data for the agent backend.',
    },
  )

  // Register all tools (Tasks 2.2 – 2.6)
  registerMatterTools(server)
  registerClientTools(server)
  registerDocumentTools(server)
  registerConversationTools(server)
  registerAuditTools(server)

  return server
}
