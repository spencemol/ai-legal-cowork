import { FastifyInstance } from 'fastify'
import { z } from 'zod'
import { prisma } from '../db'
import { hashPassword, verifyPassword } from '../auth/password'
import { authenticate } from '../middleware/authenticate'
import { RegisterSchema, LoginSchema } from '../schemas/auth'
import { isOidcConfigured, getOidcConfig, validateOidcToken } from '../auth/strategies/oidc'

const SsoCallbackSchema = z.object({
  id_token: z.string().min(1),
})

export default async function authRoutes(fastify: FastifyInstance): Promise<void> {
  // POST /auth/register — Task 1.2
  fastify.post('/register', async (request, reply) => {
    const parsed = RegisterSchema.safeParse(request.body)
    if (!parsed.success) {
      const errors: unknown[] = parsed.error.issues
      return reply.code(400).send({ message: 'Validation error', errors })
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
      const errors: unknown[] = parsed.error.issues
      return reply.code(400).send({ message: 'Validation error', errors })
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

  // ── SSO / OIDC routes — Task 9.1 ─────────────────────────────────────────

  // GET /auth/sso/config — returns whether SSO is configured for this deployment
  fastify.get('/sso/config', async (_request, reply) => {
    const configured = isOidcConfigured()
    const config = getOidcConfig()
    return reply.code(200).send({
      sso_enabled: configured,
      provider: configured ? config?.issuer : null,
      strategy: process.env.AUTH_STRATEGY ?? 'password',
    })
  })

  // POST /auth/sso/callback — validates OIDC ID token, issues internal JWT
  fastify.post('/sso/callback', async (request, reply) => {
    const parsed = SsoCallbackSchema.safeParse(request.body)
    if (!parsed.success) {
      return reply.code(400).send({ message: 'Validation error', errors: parsed.error.issues })
    }

    const config = getOidcConfig()
    if (!config) {
      return reply.code(503).send({ message: 'SSO not configured' })
    }

    let claims
    try {
      claims = validateOidcToken(parsed.data.id_token, config)
    } catch (err) {
      return reply.code(401).send({ message: (err as Error).message })
    }

    // Look up or provision user by SSO subject / email
    let user = await prisma.user.findUnique({ where: { email: claims.email } })
    if (!user) {
      // Auto-provision SSO user
      user = await prisma.user.create({
        data: {
          email: claims.email,
          name: claims.name ?? claims.email,
          role: (claims.role as 'attorney' | 'paralegal' | 'partner') ?? 'attorney',
          password_hash: null,
          sso_provider: config.issuer,
          sso_id: claims.sub,
        },
      })
    }

    const payload = { id: user.id, email: user.email, role: user.role }
    const access_token = fastify.jwt.sign(payload, { expiresIn: '1h' })
    const refresh_token = fastify.jwt.sign(payload, { expiresIn: '7d' })

    return reply.code(200).send({ access_token, refresh_token })
  })
}
