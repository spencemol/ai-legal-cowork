/**
 * OIDC token validation stub (Task 9.1).
 *
 * Validates an OIDC ID token (JWT) issued by an external identity provider and
 * extracts the internal user claims needed to issue an internal JWT.
 *
 * In production this would call the provider's JWKS endpoint to verify the
 * signature.  In this stub we:
 *   - Check token structure / expiry using the `jsonwebtoken` library.
 *   - Read OIDC_ISSUER and OIDC_AUDIENCE from the environment.
 *   - Return a normalised claim set that auth.ts can use to issue an internal JWT.
 */

import jwt from 'jsonwebtoken'

export interface OidcConfig {
  issuer: string
  audience: string
  /** Public key or shared secret for ID-token verification.
   *  In production this comes from the provider's JWKS endpoint. */
  secret: string
}

export interface OidcClaims {
  sub: string
  email: string
  name?: string
  role?: string
}

/** Read OIDC config from environment variables. */
export function getOidcConfig(): OidcConfig | null {
  const issuer = process.env.OIDC_ISSUER
  const audience = process.env.OIDC_AUDIENCE
  const secret = process.env.OIDC_SECRET ?? process.env.JWT_SECRET

  if (!issuer || !audience || !secret) return null

  return { issuer, audience, secret }
}

/** Returns true when OIDC is configured (all required env vars present). */
export function isOidcConfigured(): boolean {
  return getOidcConfig() !== null
}

/**
 * Validate an OIDC ID token and return normalised claims.
 *
 * Throws if the token is invalid, expired, or doesn't match issuer/audience.
 */
export function validateOidcToken(idToken: string, config: OidcConfig): OidcClaims {
  let decoded: jwt.JwtPayload

  try {
    decoded = jwt.verify(idToken, config.secret, {
      issuer: config.issuer,
      audience: config.audience,
    }) as jwt.JwtPayload
  } catch (err) {
    throw new Error(`Invalid OIDC token: ${(err as Error).message}`)
  }

  const sub = decoded.sub
  const email = decoded.email as string | undefined

  if (!sub || !email) {
    throw new Error('OIDC token missing required claims: sub, email')
  }

  return {
    sub,
    email,
    name: decoded.name as string | undefined,
    // Provider may send role as a custom claim; default to 'attorney'
    role: (decoded.role as string | undefined) ?? 'attorney',
  }
}
