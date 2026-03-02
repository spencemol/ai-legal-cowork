import { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { authenticate } from '../middleware/authenticate'
import { requireRoles } from '../middleware/rbac'
import { requireMatterAccess } from '../middleware/matterAccess'
import {
  CreateMatterSchema,
  UpdateMatterSchema,
  CreateAssignmentSchema,
} from '../schemas/matters'

export default async function mattersRoutes(fastify: FastifyInstance): Promise<void> {
  const authOnly = [authenticate]
  const authAttorney = [authenticate, requireRoles(['attorney', 'partner'])]

  // ─── Matters CRUD — Task 1.8 ───────────────────────────────────────────────

  // POST /matters
  fastify.post('/matters', { preHandler: authAttorney }, async (request, reply) => {
    const parsed = CreateMatterSchema.safeParse(request.body)
    if (!parsed.success) {
      const errors: unknown[] = parsed.error.errors
      return reply.code(400).send({ message: 'Validation error', errors })
    }
    const user = request.user as { id: string }
    const matter = await prisma.matter.create({
      data: { ...parsed.data, created_by_id: user.id },
    })
    return reply.code(201).send(matter)
  })

  // GET /matters
  fastify.get('/matters', { preHandler: authOnly }, async (request, reply) => {
    const matters = await prisma.matter.findMany()
    return reply.code(200).send(matters)
  })

  // GET /matters/:id
  fastify.get(
    '/matters/:id',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id } = request.params as { id: string }
      const matter = await prisma.matter.findUnique({ where: { id } })
      if (!matter) return reply.code(404).send({ message: 'Matter not found' })
      return reply.code(200).send(matter)
    },
  )

  // PUT /matters/:id
  fastify.put(
    '/matters/:id',
    { preHandler: [authenticate, requireMatterAccess({ writeAccess: true })] },
    async (request, reply) => {
      const { id } = request.params as { id: string }
      const parsed = UpdateMatterSchema.safeParse(request.body)
      if (!parsed.success) {
        const errors: unknown[] = parsed.error.errors
        return reply.code(400).send({ message: 'Validation error', errors })
      }
      const matter = await prisma.matter.update({ where: { id }, data: parsed.data })
      return reply.code(200).send(matter)
    },
  )

  // ─── Matter Assignments — Task 1.10 ───────────────────────────────────────

  // POST /matters/:id/assignments
  fastify.post(
    '/matters/:id/assignments',
    { preHandler: [authenticate, requireRoles(['attorney', 'partner']), requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const parsed = CreateAssignmentSchema.safeParse(request.body)
      if (!parsed.success) {
        const errors: unknown[] = parsed.error.errors
        return reply.code(400).send({ message: 'Validation error', errors })
      }
      const assignment = await prisma.matterAssignment.create({
        data: { matter_id, ...parsed.data },
      })
      return reply.code(201).send(assignment)
    },
  )

  // GET /matters/:id/assignments
  fastify.get(
    '/matters/:id/assignments',
    { preHandler: [authenticate, requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id } = request.params as { id: string }
      const assignments = await prisma.matterAssignment.findMany({
        where: { matter_id },
        include: { user: { select: { id: true, name: true, email: true, role: true } } },
      })
      return reply.code(200).send(assignments)
    },
  )

  // DELETE /matters/:id/assignments/:userId
  fastify.delete(
    '/matters/:id/assignments/:userId',
    { preHandler: [authenticate, requireRoles(['attorney', 'partner']), requireMatterAccess()] },
    async (request, reply) => {
      const { id: matter_id, userId: user_id } = request.params as {
        id: string
        userId: string
      }
      await prisma.matterAssignment.delete({
        where: { matter_id_user_id: { matter_id, user_id } },
      })
      return reply.code(204).send()
    },
  )
}
