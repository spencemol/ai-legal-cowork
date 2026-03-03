import { useState } from 'react'
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

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const login = useAuthStore((s) => s.login)

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

  return (
    <div className="login-page">
      <h1>Legal AI Tool</h1>
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
