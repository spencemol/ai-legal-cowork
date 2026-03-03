import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { Citation } from '../../types'

const mockCitation: Citation = {
  doc_id: 'doc-1',
  chunk_id: 'chunk-123',
  text_snippet: 'The statute of limitations for contract claims is three years.',
  page: 42,
}

describe('CitationLink (Task 5.9)', () => {
  it('renders a citation number link', async () => {
    const { CitationLink } = await import('./CitationLink')
    render(<CitationLink citation={mockCitation} index={1} onCitationClick={vi.fn()} />)

    expect(screen.getByRole('button', { name: /\[1\]/i })).toBeInTheDocument()
  })

  it('shows text snippet on hover (title attribute)', async () => {
    const { CitationLink } = await import('./CitationLink')
    render(<CitationLink citation={mockCitation} index={1} onCitationClick={vi.fn()} />)

    const link = screen.getByRole('button', { name: /\[1\]/i })
    expect(link).toHaveAttribute('title', expect.stringContaining(mockCitation.text_snippet))
  })

  it('calls onCitationClick with citation when clicked', async () => {
    const onClick = vi.fn()
    const { CitationLink } = await import('./CitationLink')
    render(<CitationLink citation={mockCitation} index={1} onCitationClick={onClick} />)

    fireEvent.click(screen.getByRole('button', { name: /\[1\]/i }))

    expect(onClick).toHaveBeenCalledWith(mockCitation)
  })

  it('displays page number in title when page is set', async () => {
    const { CitationLink } = await import('./CitationLink')
    render(<CitationLink citation={mockCitation} index={2} onCitationClick={vi.fn()} />)

    const link = screen.getByRole('button', { name: /\[2\]/i })
    expect(link).toHaveAttribute('title', expect.stringContaining('p. 42'))
  })

  it('renders with citation-link class', async () => {
    const { CitationLink } = await import('./CitationLink')
    const { container } = render(
      <CitationLink citation={mockCitation} index={1} onCitationClick={vi.fn()} />,
    )

    expect(container.querySelector('.citation-link')).toBeTruthy()
  })

  it('handles null page gracefully', async () => {
    const citationNoPage: Citation = { ...mockCitation, page: null }
    const { CitationLink } = await import('./CitationLink')
    render(<CitationLink citation={citationNoPage} index={3} onCitationClick={vi.fn()} />)

    const link = screen.getByRole('button', { name: /\[3\]/i })
    expect(link).toBeInTheDocument()
    expect(link).not.toHaveAttribute('title', expect.stringContaining('p. null'))
  })
})
