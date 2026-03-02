import { FastifyRequest, FastifyReply } from 'fastify'

type Role = 'attorney' | 'paralegal' | 'partner'

export function requireRoles(roles: Role[]) {
  return async (request: FastifyRequest, reply: FastifyReply): Promise<void> => {
    const user = request.user as { role: Role }
    if (!roles.includes(user.role)) {
      void reply.code(403).send({ message: 'Forbidden: insufficient role' })
    }
  }
}
