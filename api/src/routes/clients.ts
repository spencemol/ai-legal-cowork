import { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { authenticate } from '../middleware/authenticate'
import { requireMatterAccess } from '../middleware/matterAccess'
import { CreateClientSchema, LinkClientSchema } from '../schemas/matters'

export default async function clientsRoutes(fastify: FastifyInstance): Promise<void> {
  // ─── Task 1.9 — Client CRUD ───────────────────────────────────────────────

  // POST /clients
  fastify.post('/clients', { preHandler: [authenticate] }, async (request, reply) => {
    const parsed = CreateClientSchema.safeParse(request.body)
    if (!parsed.success) {
      return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
    }
    const client = await prisma.client.create({ data: parsed.data })
    return reply.code(201).send(client)
  })

  // GET /clients/:id
  fastify.get('/clients/:id', { preHandler: [authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string }
    const client = await prisma.client.findUnique({ where: { id } })
    if (!client) return reply.code(404).send({ message: 'Client not found' })
    return reply.code(200).send(client)
  })

  // ─── Task 1.9 — MatterClient link/unlink ─────────────────────────────────

  // POST /matters/:id/clients
  fastify.post(
    '/matters/:id/clients',
    { preHandler: [authenticate, requireMatterAccess({ writeAccess: true })] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const parsed = LinkClientSchema.safeParse(request.body)
      if (!parsed.success) {
        return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
      }
      const link = await prisma.matterClient.create({
        data: { matter_id, client_id: parsed.data.client_id },
      })
      return reply.code(200).send(link)
    },
  )

  // DELETE /matters/:id/clients/:clientId
  fastify.delete(
    '/matters/:id/clients/:clientId',
    { preHandler: [authenticate, requireMatterAccess({ writeAccess: true })] },
    async (request, reply) => {
      const { id: matter_id, clientId: client_id } = request.params as {
        id: string
        clientId: string
      }
      await prisma.matterClient.delete({
        where: { matter_id_client_id: { matter_id, client_id } },
      })
      return reply.code(204).send()
    },
  )

  // GET /matters/:id/clients
  fastify.get(
    '/matters/:id/clients',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const links = await prisma.matterClient.findMany({
        where: { matter_id },
        include: { client: true },
      })
      const clients = links.map((l) => l.client)
      return reply.code(200).send(clients)
    },
  )
}
