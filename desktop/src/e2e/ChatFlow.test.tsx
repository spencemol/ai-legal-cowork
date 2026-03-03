/**
 * Phase 6 — Tasks 6.4 & 6.5: Chat flow and citation viewer E2E behavioral tests.
 *
 * Task 6.4 — Full chat flow:
 *   - Authenticated user selects matter and opens chat
 *   - Types a question and submits
 *   - SSE tokens stream in and render progressively
 *   - Citations appear after the stream completes
 *
 * Task 6.5 — Citation click → document viewer:
 *   - Clicking a citation button opens the DocumentViewer
 *   - DocumentViewer fetches and displays the referenced document
 *   - The cited chunk is highlighted in the viewer
 *   - Closing the viewer dismisses it
 *
 * These are behavioral component tests using RTL — no real browser or Tauri required.
 * All HTTP calls (fetch + SSE) are mocked via vi.fn().
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'

// ---------------------------------------------------------------------------
// Global fetch mock
// ---------------------------------------------------------------------------

const mockFetch = vi.fn()
global.fetch = mockFetch

// ---------------------------------------------------------------------------
// SSE client mock — controllable token/citation delivery
// ---------------------------------------------------------------------------

let capturedTokenCallback: ((token: string) => void) | null = null
let capturedCitationsCallback: ((citations: unknown[]) => void) | null = null
let capturedErrorCallback: ((err: Error) => void) | null = null
let mockConnectFn = vi.fn().mockResolvedValue(undefined)
let mockDisconnectFn = vi.fn()

vi.mock('../services/sseClient', () => ({
  createSSEClient: vi.fn().mockImplementation(() => ({
    onToken: vi.fn().mockImplementation((cb: (token: string) => void) => {
      capturedTokenCallback = cb
    }),
    onCitations: vi.fn().mockImplementation((cb: (citations: unknown[]) => void) => {
      capturedCitationsCallback = cb
    }),
    onError: vi.fn().mockImplementation((cb: (err: Error) => void) => {
      capturedErrorCallback = cb
    }),
    connect: mockConnectFn,
    disconnect: mockDisconnectFn,
  })),
}))

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const MOCK_TOKEN = 'test-jwt-token-phase6'

const MOCK_MATTER = {
  id: 'matter-e2e-001',
  title: 'Smith v. Jones — Breach of Contract',
  caseNumber: '2024-E2E-001',
  status: 'active',
}

const MOCK_CONVERSATION = {
  id: 'conv-e2e-001',
  title: 'E2E Test Chat',
  matterId: 'matter-e2e-001',
  createdAt: '2024-01-01T00:00:00Z',
}

const MOCK_CITATION = {
  doc_id: 'doc-e2e-001',
  chunk_id: 'doc-e2e-001_0',
  text_snippet: 'The plaintiff alleges breach of contract on January 1, 2024.',
  page: 1,
}

const MOCK_DOCUMENT = {
  id: 'doc-e2e-001',
  title: 'Smith v. Jones — Case Brief',
  content:
    'Introduction paragraph.\n' +
    'The plaintiff alleges breach of contract on January 1, 2024.\n' +
    'Conclusion paragraph.',
  mimeType: 'application/pdf',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupAuthAndMatter() {
  useAuthStore.setState({
    token: MOCK_TOKEN,
    user: { id: 'user-001', email: 'attorney@firm.com', name: 'Test Attorney', role: 'attorney' },
  })
  useChatStore.setState({
    activeMatter: MOCK_MATTER,
    activeConversation: MOCK_CONVERSATION,
    messages: [],
    conversations: [MOCK_CONVERSATION],
    searchQuery: '',
  })
}

function makeMessageSaveResponse() {
  return {
    ok: true,
    status: 201,
    json: async () => ({
      data: { id: 'msg-001', role: 'user', content: 'Test', createdAt: '2024-01-01T00:00:00Z' },
    }),
  }
}

/** Find a citation button by its numeric index. Citations render as [, n, ] text nodes. */
function getCitationButton(index: number): HTMLElement | undefined {
  return screen
    .getAllByRole('button')
    .find((btn) => btn.textContent?.replace(/\s/g, '') === `[${index}]`)
}

// ---------------------------------------------------------------------------
// Task 6.4 — Login → select matter → ask question → streamed response
// ---------------------------------------------------------------------------

describe('Phase 6 Task 6.4 — Chat flow: question → streamed response → citations', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    capturedTokenCallback = null
    capturedCitationsCallback = null
    capturedErrorCallback = null
    mockConnectFn = vi.fn().mockResolvedValue(undefined)
    mockDisconnectFn = vi.fn()
    setupAuthAndMatter()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders chat input and send button when matter and conversation are active', async () => {
    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('chat window is in active state when conversation is selected (no empty placeholder)', async () => {
    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    const { container } = render(<ChatWindow />)

    // Active chat window rendered — not the "select a conversation" placeholder
    expect(container.querySelector('.chat-window')).toBeInTheDocument()
    expect(container.querySelector('.chat-window-empty')).not.toBeInTheDocument()
  })

  it('appends user message to chat immediately after send', async () => {
    mockFetch.mockResolvedValueOnce(makeMessageSaveResponse())

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'What are the key facts in this case?' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText('What are the key facts in this case?')).toBeInTheDocument()
    })
  })

  it('clears the input field after sending a message', async () => {
    mockFetch.mockResolvedValueOnce(makeMessageSaveResponse())

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'What happened?' } })
    expect(textarea.value).toBe('What happened?')

    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(textarea.value).toBe('')
    })
  })

  it('streams tokens and accumulates them in the assistant message', async () => {
    mockFetch.mockResolvedValueOnce(makeMessageSaveResponse())

    // connect delivers tokens before resolving
    mockConnectFn = vi.fn().mockImplementation(async () => {
      capturedTokenCallback?.('The ')
      capturedTokenCallback?.('contract ')
      capturedTokenCallback?.('was ')
      capturedTokenCallback?.('breached.')
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'What happened with the contract?' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /send/i }))
      await new Promise((r) => setTimeout(r, 50))
    })

    await waitFor(() => {
      const body = document.body.textContent ?? ''
      expect(body).toContain('breached')
    })
  })

  it('renders citations from store after message includes citation data', async () => {
    // Pre-populate messages with an assistant message that has citations
    useChatStore.setState({
      activeMatter: MOCK_MATTER,
      activeConversation: MOCK_CONVERSATION,
      messages: [
        { id: 'user-1', role: 'user', content: 'What are the facts?' },
        {
          id: 'asst-1',
          role: 'assistant',
          content: 'The contract was breached.',
          citations: [MOCK_CITATION],
        },
      ],
      conversations: [MOCK_CONVERSATION],
      searchQuery: '',
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    // At least one citation button should render
    await waitFor(() => {
      const btn = getCitationButton(1)
      expect(btn).toBeDefined()
    })
  })

  it('does not show SSE client when there is no active conversation', async () => {
    const { createSSEClient } = await import('../services/sseClient')

    useChatStore.setState({
      activeMatter: MOCK_MATTER,
      activeConversation: null,
      messages: [],
      conversations: [],
      searchQuery: '',
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    expect(screen.getByText(/select or create a conversation/i)).toBeInTheDocument()
    expect(createSSEClient).not.toHaveBeenCalled()
  })

  it('SSE client is initialized with the correct agents URL and auth token', async () => {
    const { createSSEClient } = await import('../services/sseClient')
    mockFetch.mockResolvedValueOnce(makeMessageSaveResponse())

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'Summarize the case.' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(createSSEClient).toHaveBeenCalledWith(
        expect.stringContaining('/chat'),
        expect.objectContaining({ matterId: MOCK_CONVERSATION.matterId }),
        MOCK_TOKEN,
      )
    })
  })
})

// ---------------------------------------------------------------------------
// Task 6.5 — Citation click → document viewer opens at correct section
// ---------------------------------------------------------------------------

describe('Phase 6 Task 6.5 — Citation click opens document viewer at correct chunk', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    setupAuthAndMatter()

    // Pre-populate with an assistant message that has a citation
    useChatStore.setState({
      activeMatter: MOCK_MATTER,
      activeConversation: MOCK_CONVERSATION,
      messages: [
        { id: 'user-1', role: 'user', content: 'What happened?' },
        {
          id: 'asst-1',
          role: 'assistant',
          content: 'The contract was breached.',
          citations: [MOCK_CITATION],
        },
      ],
      conversations: [MOCK_CONVERSATION],
      searchQuery: '',
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('clicking a citation button opens the DocumentViewer (loading state appears)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    // Citation button is rendered (text nodes: "[", "1", "]")
    await waitFor(() => {
      expect(getCitationButton(1)).toBeDefined()
    })

    fireEvent.click(getCitationButton(1)!)

    // DocumentViewer appears in some state: loading or loaded
    await waitFor(() => {
      const loadingEl = document.body.textContent?.includes('Loading document')
      const docTitle = document.body.textContent?.includes(MOCK_DOCUMENT.title)
      const closeBtn = screen.queryByRole('button', { name: /close/i })
      expect(loadingEl || docTitle || closeBtn).toBeTruthy()
    })
  })

  it('document viewer fetches the document by doc_id from the citation', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(MOCK_CITATION.doc_id),
        expect.any(Object),
      )
    })
  })

  it('document viewer shows the document title when loaded', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    await waitFor(() => {
      expect(screen.getByText(MOCK_DOCUMENT.title)).toBeInTheDocument()
    })
  })

  it('document viewer highlights the cited text snippet in the document', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    const { container } = render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    // Wait for document to fully load and highlighted-chunk to appear
    await waitFor(() => {
      expect(screen.getByText(MOCK_DOCUMENT.title)).toBeInTheDocument()
    })

    // highlighted-chunk span wraps the cited text snippet
    const highlighted = container.querySelector('.highlighted-chunk')
    expect(highlighted).not.toBeNull()
    expect(highlighted?.textContent).toContain('The plaintiff alleges breach of contract')
  })

  it('closing the document viewer dismisses it', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /close/i }))

    await waitFor(() => {
      expect(screen.queryByText(MOCK_DOCUMENT.title)).not.toBeInTheDocument()
    })
  })

  it('document viewer shows error message when document fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ error: 'Not found' }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    await waitFor(() => {
      const bodyText = document.body.textContent ?? ''
      expect(
        bodyText.toLowerCase().includes('error') || bodyText.toLowerCase().includes('failed'),
      ).toBe(true)
    })
  })

  it('document viewer passes Authorization header when fetching document', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: MOCK_DOCUMENT }),
    })

    const { ChatWindow } = await import('../components/Chat/ChatWindow')
    render(<ChatWindow />)

    await waitFor(() => expect(getCitationButton(1)).toBeDefined())
    fireEvent.click(getCitationButton(1)!)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${MOCK_TOKEN}`,
          }),
        }),
      )
    })
  })
})
