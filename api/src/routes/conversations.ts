import { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { authenticate } from '../middleware/authenticate'
import { requireMatterAccess } from '../middleware/matterAccess'
import { CreateConversationSchema, CreateMessageSchema } from '../schemas/conversations'

export default async function conversationsRoutes(fastify: FastifyInstance): Promise<void> {
  // ─── Task 1.16 — Conversations CRUD ──────────────────────────────────────

  // POST /matters/:id/conversations
  fastify.post(
    '/matters/:id/conversations',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const parsed = CreateConversationSchema.safeParse(request.body)
      if (!parsed.success) {
        const errors: unknown[] = parsed.error.issues
        return reply.code(400).send({ message: 'Validation error', errors })
      }
      const user = request.user as { id: string }
      const conversation = await prisma.conversation.create({
        data: { ...parsed.data, matter_id, created_by_id: user.id },
      })
      return reply.code(201).send(conversation)
    },
  )

  // GET /matters/:id/conversations
  fastify.get(
    '/matters/:id/conversations',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const conversations = await prisma.conversation.findMany({ where: { matter_id } })
      return reply.code(200).send(conversations)
    },
  )

  // GET /conversations/:id
  fastify.get('/conversations/:id', { preHandler: [authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string }
    const conversation = await prisma.conversation.findUnique({
      where: { id },
      include: { messages: true },
    })
    if (!conversation) return reply.code(404).send({ message: 'Conversation not found' })
    return reply.code(200).send(conversation)
  })

  // POST /conversations/:id/messages
  fastify.post(
    '/conversations/:id/messages',
    { preHandler: [authenticate] },
    async (request, reply) => {
      const { id: conversation_id } = request.params as { id: string }
      const parsed = CreateMessageSchema.safeParse(request.body)
      if (!parsed.success) {
        const errors: unknown[] = parsed.error.issues
        return reply.code(400).send({ message: 'Validation error', errors })
      }
      const message = await prisma.message.create({
        data: { ...parsed.data, conversation_id },
      })
      return reply.code(201).send(message)
    },
  )
}
