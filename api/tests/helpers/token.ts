import jwt from 'jsonwebtoken'

export const TEST_SECRET = 'test-jwt-secret'

export type TestUser = {
  id: string
  email: string
  name: string
  role: 'attorney' | 'paralegal' | 'partner'
}

export const TEST_USERS = {
  attorney: {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    email: 'attorney@firm.com',
    name: 'Test Attorney',
    role: 'attorney' as const,
  },
  paralegal: {
    id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    email: 'paralegal@firm.com',
    name: 'Test Paralegal',
    role: 'paralegal' as const,
  },
  partner: {
    id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
    email: 'partner@firm.com',
    name: 'Test Partner',
    role: 'partner' as const,
  },
}

export function signToken(user: Pick<TestUser, 'id' | 'email' | 'role'>): string {
  return jwt.sign(user, TEST_SECRET, { expiresIn: '1h' })
}

export function bearerHeader(user: Pick<TestUser, 'id' | 'email' | 'role'>): string {
  return `Bearer ${signToken(user)}`
}
