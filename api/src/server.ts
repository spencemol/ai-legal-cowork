import 'dotenv/config'
import Fastify, { FastifyInstance } from 'fastify'
import cors from '@fastify/cors'

export async function buildServer(): Promise<FastifyInstance> {
  const server = Fastify({
    logger: true,
  })

  await server.register(cors, {
    origin: true,
  })

  server.get('/health', async () => {
    return { status: 'ok', timestamp: new Date().toISOString() }
  })

  return server
}

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

void start()
