import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

const mockMatters = [
  { id: 'm1', title: 'Smith v. Jones', caseNumber: '2024-001', status: 'active' },
  { id: 'm2', title: 'Doe v. Corp', caseNumber: '2024-002', status: 'active' },
]

describe('MatterSelector (Task 5.5)', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    useAuthStore.setState({ token: 'test-token', user: { id: '1', email: 'a@b.com', name: 'A', role: 'attorney' } })
    useChatStore.setState({ activeMatter: null, conversations: [], messages: [] })
  })

  it('fetches and displays assigned matters', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockMatters }),
    })

    const { MatterSelector } = await import('./MatterSelector')
    render(<MatterSelector />)

    await waitFor(() => {
      expect(screen.getByText('Smith v. Jones')).toBeInTheDocument()
      expect(screen.getByText('Doe v. Corp')).toBeInTheDocument()
    })
  })

  it('sets active matter in store when selected', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockMatters }),
    })

    const { MatterSelector } = await import('./MatterSelector')
    render(<MatterSelector />)

    await waitFor(() => {
      expect(screen.getByText('Smith v. Jones')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Smith v. Jones'))

    const { activeMatter } = useChatStore.getState()
    expect(activeMatter).toEqual(mockMatters[0])
  })

  it('shows loading state while fetching', async () => {
    let resolveRequest: (value: unknown) => void
    mockFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )

    const { MatterSelector } = await import('./MatterSelector')
    render(<MatterSelector />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    resolveRequest!({
      ok: true,
      status: 200,
      json: async () => ({ data: mockMatters }),
    })
  })

  it('shows error state when fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' }),
    })

    const { MatterSelector } = await import('./MatterSelector')
    render(<MatterSelector />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('highlights the selected matter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockMatters }),
    })

    useChatStore.setState({ activeMatter: mockMatters[0], conversations: [], messages: [] })

    const { MatterSelector } = await import('./MatterSelector')
    render(<MatterSelector />)

    await waitFor(() => {
      const selectedItem = screen.getByText('Smith v. Jones').closest('[aria-selected]')
      expect(selectedItem).toHaveAttribute('aria-selected', 'true')
    })
  })
})
