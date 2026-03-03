import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useAuthStore } from '../../stores/authStore'

describe('AuthGuard (Task 5.4)', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null })
  })

  it('renders login fallback when not authenticated', async () => {
    const { AuthGuard } = await import('./AuthGuard')
    render(
      <AuthGuard fallback={<div>Please login</div>}>
        <div>Protected content</div>
      </AuthGuard>,
    )

    expect(screen.getByText(/please login/i)).toBeInTheDocument()
    expect(screen.queryByText(/protected content/i)).not.toBeInTheDocument()
  })

  it('renders children when authenticated', async () => {
    useAuthStore.setState({
      token: 'valid-token',
      user: { id: '1', email: 'test@example.com', name: 'Test', role: 'attorney' },
    })

    const { AuthGuard } = await import('./AuthGuard')
    render(
      <AuthGuard fallback={<div>Please login</div>}>
        <div>Protected content</div>
      </AuthGuard>,
    )

    expect(screen.getByText(/protected content/i)).toBeInTheDocument()
    expect(screen.queryByText(/please login/i)).not.toBeInTheDocument()
  })

  it('transitions from login to protected when token is set', async () => {
    const { AuthGuard } = await import('./AuthGuard')
    const { rerender } = render(
      <AuthGuard fallback={<div>Please login</div>}>
        <div>Protected content</div>
      </AuthGuard>,
    )

    expect(screen.getByText(/please login/i)).toBeInTheDocument()

    useAuthStore.setState({
      token: 'valid-token',
      user: { id: '1', email: 'a@b.com', name: 'A', role: 'attorney' },
    })

    rerender(
      <AuthGuard fallback={<div>Please login</div>}>
        <div>Protected content</div>
      </AuthGuard>,
    )

    expect(screen.getByText(/protected content/i)).toBeInTheDocument()
  })
})
