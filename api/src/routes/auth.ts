import { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { hashPassword, verifyPassword } from '../auth/password'
import { authenticate } from '../middleware/authenticate'
import { RegisterSchema, LoginSchema } from '../schemas/auth'

export default async function authRoutes(fastify: FastifyInstance): Promise<void> {
  // POST /auth/register — Task 1.2
  fastify.post('/register', async (request, reply) => {
    const parsed = RegisterSchema.safeParse(request.body)
    if (!parsed.success) {
      return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
    }

    const { email, password, name, role } = parsed.data
    const password_hash = await hashPassword(password)

    let user
    try {
      user = await prisma.user.create({
        data: { email, name, role, password_hash },
      })
    } catch (err: unknown) {
      const e = err as { code?: string }
      if (e.code === 'P2002') {
        return reply.code(409).send({ message: 'Email already in use' })
      }
      throw err
    }

    const { password_hash: _ph, ...safeUser } = user
    return reply.code(201).send(safeUser)
  })

  // POST /auth/login — Task 1.3
  fastify.post('/login', async (request, reply) => {
    const parsed = LoginSchema.safeParse(request.body)
    if (!parsed.success) {
      return reply.code(400).send({ message: 'Validation error', errors: parsed.error.errors })
    }

    const { email, password } = parsed.data

    const user = await prisma.user.findUnique({ where: { email } })
    if (!user || !user.password_hash) {
      return reply.code(401).send({ message: 'Invalid credentials' })
    }

    const valid = await verifyPassword(password, user.password_hash)
    if (!valid) {
      return reply.code(401).send({ message: 'Invalid credentials' })
    }

    const payload = { id: user.id, email: user.email, role: user.role }
    const access_token = fastify.jwt.sign(payload, { expiresIn: '1h' })
    const refresh_token = fastify.jwt.sign(payload, { expiresIn: '7d' })

    return reply.code(200).send({ access_token, refresh_token })
  })

  // GET /auth/me — Task 1.4 (JWT validation demo route)
  fastify.get('/me', { preHandler: [authenticate] }, async (request, reply) => {
    return reply.code(200).send(request.user)
  })
}
