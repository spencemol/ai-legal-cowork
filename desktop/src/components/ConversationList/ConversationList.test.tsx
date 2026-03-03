import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'

const mockFetch = vi.fn()
global.fetch = mockFetch

const mockConversations = [
  { id: 'c1', title: 'Smith v Jones research', matterId: 'm1', createdAt: '2024-01-01T10:00:00Z' },
  { id: 'c2', title: 'Contract review', matterId: 'm1', createdAt: '2024-01-02T10:00:00Z' },
  { id: 'c3', title: 'Statute of limitations analysis', matterId: 'm1', createdAt: '2024-01-03T10:00:00Z' },
]

const mockMatter = { id: 'm1', title: 'Smith v. Jones', caseNumber: '2024-001', status: 'active' }

describe('ConversationList (Tasks 5.10, 5.11, 5.14)', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    useAuthStore.setState({ token: 'test-token', user: { id: '1', email: 'a@b.com', name: 'A', role: 'attorney' } })
    useChatStore.setState({
      activeMatter: mockMatter,
      activeConversation: null,
      conversations: [],
      messages: [],
      searchQuery: '',
    })
  })

  // Task 5.10: fetch and display conversations
  it('fetches and displays conversations for active matter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByText('Smith v Jones research')).toBeInTheDocument()
      expect(screen.getByText('Contract review')).toBeInTheDocument()
    })
  })

  it('sets active conversation when clicking a conversation', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByText('Contract review')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Contract review'))

    const { activeConversation } = useChatStore.getState()
    expect(activeConversation).toEqual(mockConversations[1])
  })

  // Task 5.11: new conversation action
  it('renders a New Chat button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new chat/i })).toBeInTheDocument()
    })
  })

  it('creates a new conversation and sets it active on New Chat click', async () => {
    const newConversation = { id: 'c-new', title: 'New Chat', matterId: 'm1', createdAt: '2024-01-04T10:00:00Z' }

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: mockConversations }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ data: newConversation }),
      })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new chat/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /new chat/i }))

    await waitFor(() => {
      const { activeConversation } = useChatStore.getState()
      expect(activeConversation?.id).toBe('c-new')
    })
  })

  // Task 5.14: conversation search
  it('renders a search input', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
    })
  })

  it('filters conversations by search query', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByText('Smith v Jones research')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/search/i)
    await userEvent.type(searchInput, 'contract')

    await waitFor(() => {
      expect(screen.getByText('Contract review')).toBeInTheDocument()
      expect(screen.queryByText('Smith v Jones research')).not.toBeInTheDocument()
    })
  })

  it('shows all conversations when search is cleared', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByText('Smith v Jones research')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/search/i)
    await userEvent.type(searchInput, 'contract')
    await userEvent.clear(searchInput)

    await waitFor(() => {
      expect(screen.getByText('Smith v Jones research')).toBeInTheDocument()
      expect(screen.getByText('Contract review')).toBeInTheDocument()
    })
  })

  it('shows no results message when search matches nothing', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockConversations }),
    })

    const { ConversationList } = await import('./ConversationList')
    render(<ConversationList />)

    await waitFor(() => {
      expect(screen.getByText('Smith v Jones research')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/search/i)
    await userEvent.type(searchInput, 'xyznotfound')

    await waitFor(() => {
      expect(screen.getByText(/no conversations/i)).toBeInTheDocument()
    })
  })
})
