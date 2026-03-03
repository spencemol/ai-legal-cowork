import { useState, useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { saveToken } from '../../services/tokenStorage'
import type { User } from '../../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000'

interface LoginPageProps {
  onLoginSuccess: () => void
}

interface LoginResponse {
  token: string
  user: User
}

interface SsoConfig {
  sso_enabled: boolean
  provider: string | null
  strategy: string
}

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [ssoConfig, setSsoConfig] = useState<SsoConfig | null>(null)
  const [ssoLoading, setSsoLoading] = useState(true)
  const login = useAuthStore((s) => s.login)

  // Fetch SSO config on mount (Task 9.2)
  useEffect(() => {
    async function fetchSsoConfig() {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/sso/config`)
        if (response.ok) {
          const config: SsoConfig = await response.json()
          setSsoConfig(config)
        }
      } catch {
        // SSO config fetch failed — default to password-only
        setSsoConfig({ sso_enabled: false, provider: null, strategy: 'password' })
      } finally {
        setSsoLoading(false)
      }
    }
    void fetchSsoConfig()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({ error: 'Login failed' }))
        throw new Error((body as { error?: string }).error ?? 'Login failed')
      }

      const data: LoginResponse = await response.json()
      await saveToken(data.token)
      login(data.token, data.user)
      onLoginSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSsoLogin = () => {
    if (!ssoConfig?.provider) return
    // Open the OIDC provider URL — in production this would be the authorization endpoint
    const ssoUrl = `${ssoConfig.provider}/oauth2/authorize?client_id=${encodeURIComponent(API_BASE_URL)}&redirect_uri=${encodeURIComponent(`${API_BASE_URL}/auth/sso/callback`)}`
    window.location.href = ssoUrl
  }

  return (
    <div className="login-page">
      <h1>Legal AI Tool</h1>

      {/* SSO Button (Task 9.2) — shown only when SSO is configured */}
      {!ssoLoading && ssoConfig?.sso_enabled && (
        <div className="sso-section">
          <button
            type="button"
            className="sso-button"
            onClick={handleSsoLogin}
            disabled={isLoading}
            aria-label={`Sign in with SSO${ssoConfig.provider ? ` (${ssoConfig.provider})` : ''}`}
          >
            Sign in with SSO
            {ssoConfig.provider && (
              <span className="sso-provider-name"> ({ssoConfig.provider})</span>
            )}
          </button>
          <div className="sso-divider">
            <span>or sign in with password</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        {error && <div role="alert" className="error">{error}</div>}
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
