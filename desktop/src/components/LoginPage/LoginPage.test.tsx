import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useAuthStore } from '../../stores/authStore'

// Mock Tauri plugin store
vi.mock('@tauri-apps/plugin-store', () => ({
  Store: vi.fn().mockImplementation(() => ({
    get: vi.fn().mockResolvedValue(null),
    set: vi.fn().mockResolvedValue(undefined),
    save: vi.fn().mockResolvedValue(undefined),
  })),
}))

// Mock tokenStorage to avoid Tauri dependency
vi.mock('../../services/tokenStorage', () => ({
  saveToken: vi.fn().mockResolvedValue(undefined),
  getToken: vi.fn().mockResolvedValue(null),
  clearToken: vi.fn().mockResolvedValue(undefined),
}))

// Use vi.stubGlobal so the stub is properly tracked and restored
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('LoginPage (Task 5.3)', () => {
  const mockOnLoginSuccess = vi.fn()

  beforeEach(() => {
    mockFetch.mockReset()
    mockOnLoginSuccess.mockReset()
    useAuthStore.setState({ token: null, user: null })
  })

  afterEach(() => {
    cleanup()
  })

  it('renders email and password fields', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('renders a submit button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows error message on invalid credentials', async () => {
    // Call [1]: SSO config → disabled
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    // Call [2]: login → 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ error: 'Invalid credentials' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    // Wait for SSO config fetch to complete before submitting
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    await userEvent.type(screen.getByLabelText(/email/i), 'bad@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  it('calls onLoginSuccess on valid credentials', async () => {
    const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ token: 'valid-jwt', user: mockUser }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'correctpassword')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockOnLoginSuccess).toHaveBeenCalled()
    })
  })

  it('stores JWT in auth store on successful login', async () => {
    const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ token: 'valid-jwt', user: mockUser }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'correctpassword')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      const { token } = useAuthStore.getState()
      expect(token).toBe('valid-jwt')
    })
  })

  it('disables submit button while loading', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })
    let resolveRequest: (value: unknown) => void
    mockFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'password')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    })

    resolveRequest!({
      ok: true,
      status: 200,
      json: async () => ({ token: 'jwt', user: { id: '1', email: 'test@example.com', name: 'Test', role: 'attorney' } }),
    })
  })
})

// ── Task 9.2 — SSO Login Flow ─────────────────────────────────────────────────

describe('LoginPage — SSO (Task 9.2)', () => {
  const mockOnLoginSuccess = vi.fn()

  beforeEach(() => {
    mockFetch.mockReset()
    mockOnLoginSuccess.mockReset()
    useAuthStore.setState({ token: null, user: null })
  })

  afterEach(() => {
    cleanup()
  })

  it('does NOT show SSO button when SSO is disabled', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    // Wait for SSO config fetch to resolve so ssoLoading becomes false
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    expect(screen.queryByRole('button', { name: /sign in with sso/i })).not.toBeInTheDocument()
  })

  it('shows SSO button when SSO is enabled', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: true, provider: 'https://sso.firm-example.com', strategy: 'oidc' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in with sso/i })).toBeInTheDocument()
    })
  })

  it('shows provider name in SSO button when provider is configured', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: true, provider: 'https://sso.firm-example.com', strategy: 'oidc' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => {
      const ssoButton = screen.getByRole('button', { name: /sign in with sso/i })
      expect(ssoButton).toBeInTheDocument()
      expect(ssoButton.textContent).toContain('sso.firm-example.com')
    })
  })

  it('password form is still visible when SSO is enabled (fallback)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: true, provider: 'https://sso.firm-example.com', strategy: 'oidc' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in with sso/i })).toBeInTheDocument()
    })

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^sign in$/i })).toBeInTheDocument()
  })

  it('does NOT show SSO button while SSO config is still loading', async () => {
    // Never resolves — ssoLoading stays true
    mockFetch.mockReturnValueOnce(new Promise(() => {}))

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    // ssoLoading=true → no SSO button rendered yet
    expect(screen.queryByRole('button', { name: /sign in with sso/i })).not.toBeInTheDocument()
  })

  it('shows no SSO button when /auth/sso/config fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /sign in with sso/i })).not.toBeInTheDocument()
    })
  })

  it('calls /auth/sso/config on component mount', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sso_enabled: false, provider: null, strategy: 'password' }),
    })

    const { LoginPage } = await import('./LoginPage')
    render(<LoginPage onLoginSuccess={mockOnLoginSuccess} />)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/sso/config'),
      )
    })
  })
})
