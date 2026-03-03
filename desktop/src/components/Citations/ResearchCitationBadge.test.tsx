/**
 * Phase 8 Task 8.1 — ResearchCitationBadge component tests.
 *
 * Verifies:
 * - Source type badge renders with correct text and color class for each source type:
 *     firm → "Internal" badge (badge-internal)
 *     web  → "Web" badge (badge-web)
 *     westlaw/lexisnexis → "Legal DB" badge (badge-legal-db)
 * - Firm citation renders a numbered [N] link
 * - Web citation renders the URL as the link text
 * - Legal DB citation renders the citation string
 * - Hover tooltip includes the text_snippet
 * - Click handler invoked with citation object
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { Citation } from '../../types'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const firmCitation: Citation = {
  doc_id: 'doc-firm-1',
  chunk_id: 'chunk-firm-1',
  text_snippet: 'The retainer agreement was signed on 2024-01-15.',
  page: 3,
  source: 'firm',
  title: 'Retainer Agreement',
}

const webCitation: Citation = {
  doc_id: '',
  chunk_id: 'web-1',
  text_snippet: 'Court rules updated in 2024.',
  page: null,
  source: 'web',
  url: 'https://example.com/court-rules',
  title: 'Court Rules 2024',
}

const westlawCitation: Citation = {
  doc_id: '',
  chunk_id: 'wl-1',
  text_snippet: 'Smith v. Jones, 123 F.3d 456 (2024).',
  page: null,
  source: 'westlaw',
  citation: 'Smith v. Jones, 123 F.3d 456 (2024)',
  title: 'Smith v. Jones',
}

const lexisCitation: Citation = {
  doc_id: '',
  chunk_id: 'ln-1',
  text_snippet: 'Doe v. Roe, 789 F.2d 012 (2023).',
  page: null,
  source: 'lexisnexis',
  citation: 'Doe v. Roe, 789 F.2d 012 (2023)',
}

const unknownCitation: Citation = {
  doc_id: 'doc-x',
  chunk_id: 'chunk-x',
  text_snippet: 'Some snippet.',
  page: null,
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ResearchCitationBadge (Phase 8 Task 8.1)', () => {
  // ---- Firm / Internal ----

  it('renders "Internal" badge for firm source', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={firmCitation} index={1} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText('Internal')).toBeInTheDocument()
  })

  it('firm badge has badge-internal CSS class', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    const { container } = render(
      <ResearchCitationBadge citation={firmCitation} index={1} onCitationClick={vi.fn()} />,
    )
    expect(container.querySelector('.badge-internal')).not.toBeNull()
  })

  it('firm citation renders numbered link [1]', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={firmCitation} index={1} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByRole('button', { name: /\[1\]/i })).toBeInTheDocument()
  })

  // ---- Web ----

  it('renders "Web" badge for web source', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={webCitation} index={2} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText('Web')).toBeInTheDocument()
  })

  it('web badge has badge-web CSS class', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    const { container } = render(
      <ResearchCitationBadge citation={webCitation} index={2} onCitationClick={vi.fn()} />,
    )
    expect(container.querySelector('.badge-web')).not.toBeNull()
  })

  it('web citation displays URL as link text', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={webCitation} index={2} onCitationClick={vi.fn()} />,
    )
    const btn = screen.getByRole('button', { name: /example\.com/i })
    expect(btn).toBeInTheDocument()
  })

  // ---- Legal DB (westlaw) ----

  it('renders "Legal DB" badge for westlaw source', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={westlawCitation} index={3} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText('Legal DB')).toBeInTheDocument()
  })

  it('westlaw badge has badge-legal-db CSS class', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    const { container } = render(
      <ResearchCitationBadge citation={westlawCitation} index={3} onCitationClick={vi.fn()} />,
    )
    expect(container.querySelector('.badge-legal-db')).not.toBeNull()
  })

  it('westlaw citation displays citation string as link text', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={westlawCitation} index={3} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText(westlawCitation.citation!)).toBeInTheDocument()
  })

  // ---- Legal DB (lexisnexis) ----

  it('renders "Legal DB" badge for lexisnexis source', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={lexisCitation} index={4} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText('Legal DB')).toBeInTheDocument()
  })

  it('lexisnexis badge has badge-legal-db CSS class', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    const { container } = render(
      <ResearchCitationBadge citation={lexisCitation} index={4} onCitationClick={vi.fn()} />,
    )
    expect(container.querySelector('.badge-legal-db')).not.toBeNull()
  })

  // ---- Tooltip / snippet ----

  it('button has title attribute containing text_snippet', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={firmCitation} index={1} onCitationClick={vi.fn()} />,
    )
    const btn = screen.getByRole('button', { name: /\[1\]/i })
    expect(btn).toHaveAttribute('title', expect.stringContaining(firmCitation.text_snippet))
  })

  it('web citation button has title attribute containing text_snippet', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={webCitation} index={2} onCitationClick={vi.fn()} />,
    )
    const btn = screen.getByRole('button', { name: /example\.com/i })
    expect(btn).toHaveAttribute('title', expect.stringContaining(webCitation.text_snippet))
  })

  // ---- Click handler ----

  it('calls onCitationClick with citation when firm link is clicked', async () => {
    const onClick = vi.fn()
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(<ResearchCitationBadge citation={firmCitation} index={1} onCitationClick={onClick} />)

    fireEvent.click(screen.getByRole('button', { name: /\[1\]/i }))
    expect(onClick).toHaveBeenCalledWith(firmCitation)
  })

  it('calls onCitationClick with citation when web link is clicked', async () => {
    const onClick = vi.fn()
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(<ResearchCitationBadge citation={webCitation} index={2} onCitationClick={onClick} />)

    fireEvent.click(screen.getByRole('button', { name: /example\.com/i }))
    expect(onClick).toHaveBeenCalledWith(webCitation)
  })

  // ---- Unknown source fallback ----

  it('renders "Internal" badge when source field is absent (fallback)', async () => {
    const { ResearchCitationBadge } = await import('./ResearchCitationBadge')
    render(
      <ResearchCitationBadge citation={unknownCitation} index={5} onCitationClick={vi.fn()} />,
    )
    expect(screen.getByText('Internal')).toBeInTheDocument()
  })
})
