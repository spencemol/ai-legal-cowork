import { FastifyRequest, FastifyReply } from 'fastify'
import { prisma } from '../db'

interface MatterAccessOptions {
  /** If true, read_only users are rejected */
  writeAccess?: boolean
}

export function requireMatterAccess(options: MatterAccessOptions = {}) {
  return async (request: FastifyRequest, reply: FastifyReply): Promise<void> => {
    const user = request.user as { id: string; role: 'attorney' | 'paralegal' | 'partner' }

    // Partners have global read/write access to all matters
    if (user.role === 'partner') return

    const params = request.params as Record<string, string>
    const matterId = params.id ?? params.matterId

    if (!matterId) return

    const assignment = await prisma.matterAssignment.findFirst({
      where: { matter_id: matterId, user_id: user.id },
    })

    if (!assignment) {
      reply.code(403).send({ message: 'Forbidden: not assigned to this matter' })
      return
    }

    if (options.writeAccess && assignment.access_level === 'read_only') {
      reply.code(403).send({ message: 'Forbidden: read-only access level' })
    }
  }
}
