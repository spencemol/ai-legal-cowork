import 'dotenv/config'
import Fastify, { FastifyInstance, FastifyError, FastifyRequest, FastifyReply } from 'fastify'
import cors from '@fastify/cors'
import jwt from '@fastify/jwt'
import { ZodError } from 'zod'
import authRoutes from './routes/auth'
import mattersRoutes from './routes/matters'
import clientsRoutes from './routes/clients'
import documentsRoutes from './routes/documents'
import conversationsRoutes from './routes/conversations'

// ─── Task 1.20 — Global error handler ────────────────────────────────────────
function errorHandler(
  error: FastifyError,
  _request: FastifyRequest,
  reply: FastifyReply,
): void {
  if (error instanceof ZodError) {
    void reply.code(400).send({ message: 'Validation error', errors: error.errors })
    return
  }

  const statusCode = error.statusCode ?? 500
  const message = statusCode < 500 ? error.message : 'Internal Server Error'
  void reply.code(statusCode).send({ message })
}

// ─── Server factory ──────────────────────────────────────────────────────────
export async function buildServer(): Promise<FastifyInstance> {
  const server = Fastify({
    logger: process.env.NODE_ENV !== 'test',
  })

  // Plugins
  await server.register(cors, { origin: true })
  await server.register(jwt, {
    secret: process.env.JWT_SECRET ?? 'development-secret-change-in-production',
  })

  // Routes
  await server.register(authRoutes, { prefix: '/auth' })
  await server.register(mattersRoutes)
  await server.register(clientsRoutes)
  await server.register(documentsRoutes)
  await server.register(conversationsRoutes)

  // Health check
  server.get('/health', async () => {
    return { status: 'ok', timestamp: new Date().toISOString() }
  })

  // Error-test route (used by error-handling.test.ts, Task 1.20)
  server.get('/error-test', async () => {
    throw new Error('Intentional test error')
  })

  // Global error handler
  server.setErrorHandler(errorHandler)

  return server
}

// ─── Entry point ─────────────────────────────────────────────────────────────
async function start(): Promise<void> {
  const server = await buildServer()
  try {
    const port = parseInt(process.env.PORT ?? '3000', 10)
    const host = process.env.HOST ?? '0.0.0.0'
    await server.listen({ port, host })
  } catch (err) {
    server.log.error(err)
    process.exit(1)
  }
}

// Only start the server when this file is run directly (not when imported by tests)
if (require.main === module) {
  void start()
}
