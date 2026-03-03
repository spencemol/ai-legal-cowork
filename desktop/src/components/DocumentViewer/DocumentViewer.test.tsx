import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import type { Citation } from '../../types'

const mockFetch = vi.fn()
global.fetch = mockFetch

const mockDocument = {
  id: 'doc-1',
  title: 'Smith v. Jones Contract',
  content: 'SECTION 1. Introduction\n\nThis contract establishes...\n\nSECTION 2. Terms\n\nThe statute of limitations for contract claims is three years.\n\nSECTION 3. Termination\n\nEither party may terminate...',
  mimeType: 'text/plain',
}

const mockCitation: Citation = {
  doc_id: 'doc-1',
  chunk_id: 'chunk-123',
  text_snippet: 'The statute of limitations for contract claims is three years.',
  page: 2,
}

describe('DocumentViewer (Tasks 5.12, 5.13)', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  // Task 5.12: split-view document viewer
  it('renders nothing when no citation is provided', async () => {
    const { DocumentViewer } = await import('./DocumentViewer')
    const { container } = render(<DocumentViewer citation={null} onClose={vi.fn()} />)

    expect(container.querySelector('.document-viewer')).toBeFalsy()
  })

  it('renders document viewer panel when citation is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockDocument }),
    })

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    await waitFor(() => {
      expect(document.querySelector('.document-viewer')).toBeTruthy()
    })
  })

  it('fetches and displays document content when citation is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockDocument }),
    })

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Smith v. Jones Contract')).toBeInTheDocument()
    })
  })

  it('renders a close button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockDocument }),
    })

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })
  })

  it('calls onClose when close button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockDocument }),
    })

    const onClose = vi.fn()
    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={onClose} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalled()
  })

  // Task 5.13: navigation to referenced chunk
  it('highlights the cited text snippet in the document', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ data: mockDocument }),
    })

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    await waitFor(() => {
      const highlighted = document.querySelector('.highlighted-chunk')
      expect(highlighted).toBeTruthy()
      expect(highlighted?.textContent).toContain('The statute of limitations')
    })
  })

  it('shows loading indicator while fetching document', async () => {
    let resolveRequest: (value: unknown) => void
    mockFetch.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    await act(async () => {
      resolveRequest!({
        ok: true,
        status: 200,
        json: async () => ({ data: mockDocument }),
      })
    })
  })

  it('shows error when document fetch fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ error: 'Document not found' }),
    })

    const { DocumentViewer } = await import('./DocumentViewer')
    render(<DocumentViewer citation={mockCitation} onClose={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })
})
