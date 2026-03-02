import { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { authenticate } from '../middleware/authenticate'
import { requireMatterAccess } from '../middleware/matterAccess'
import { RegisterDocumentSchema, UpdateDocumentStatusSchema } from '../schemas/documents'

export default async function documentsRoutes(fastify: FastifyInstance): Promise<void> {
  // ─── Task 1.14 — Documents CRUD ──────────────────────────────────────────

  // POST /matters/:id/documents
  fastify.post(
    '/matters/:id/documents',
    { preHandler: [authenticate, requireMatterAccess({ writeAccess: true })] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const parsed = RegisterDocumentSchema.safeParse(request.body)
      if (!parsed.success) {
        return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
      }
      const user = request.user as { id: string }
      const doc = await prisma.document.create({
        data: { ...parsed.data, matter_id, uploaded_by_id: user.id },
      })
      return reply.code(201).send(doc)
    },
  )

  // GET /matters/:id/documents
  fastify.get(
    '/matters/:id/documents',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const docs = await prisma.document.findMany({ where: { matter_id } })
      return reply.code(200).send(docs)
    },
  )

  // GET /documents/:id
  fastify.get('/documents/:id', { preHandler: [authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string }
    const doc = await prisma.document.findUnique({ where: { id } })
    if (!doc) return reply.code(404).send({ message: 'Document not found' })
    return reply.code(200).send(doc)
  })

  // PATCH /documents/:id/status
  fastify.patch(
    '/documents/:id/status',
    { preHandler: [authenticate] },
    async (request, reply) => {
      const { id } = request.params as { id: string }
      const parsed = UpdateDocumentStatusSchema.safeParse(request.body)
      if (!parsed.success) {
        return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
      }
      const doc = await prisma.document.update({ where: { id }, data: { status: parsed.data.status } })
      return reply.code(200).send(doc)
    },
  )
}
