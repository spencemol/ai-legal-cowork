/**
 * Phase 8 Task 8.2 — DocumentGenPanel component tests.
 *
 * Verifies:
 * - Template dropdown renders with expected options
 * - Selecting "freeform" shows a free-text prompt input
 * - Selecting a real template hides the freeform prompt input
 * - "Generate" button is present and clickable
 * - Clicking Generate calls the onGenerate callback with correct payload
 * - Export format prop is forwarded in the generation request
 * - Matter ID is included in the request when provided
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

describe('DocumentGenPanel (Phase 8 Task 8.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders a template selector dropdown', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('template dropdown contains expected options', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    const select = screen.getByRole('combobox')
    const options = Array.from((select as HTMLSelectElement).options).map((o) => o.value)
    expect(options).toContain('engagement_letter')
    expect(options).toContain('nda')
    expect(options).toContain('motion')
    expect(options).toContain('freeform')
  })

  it('does not show freeform prompt when a template is selected (non-freeform)', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'nda' } })

    expect(screen.queryByPlaceholderText(/describe/i)).not.toBeInTheDocument()
  })

  it('shows freeform prompt textarea when "freeform" is selected', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'freeform' } })

    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders a "Generate" button', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument()
  })

  it('calls onGenerate with template name and matterId when a template is selected', async () => {
    const onGenerate = vi.fn().mockResolvedValue({ jobId: 'job-1' })
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-001" format="docx" onGenerate={onGenerate} />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'nda' } })
    fireEvent.click(screen.getByRole('button', { name: /generate/i }))

    await waitFor(() => {
      expect(onGenerate).toHaveBeenCalledWith(
        expect.objectContaining({
          matterId: 'matter-001',
          templateName: 'nda',
          format: 'docx',
        }),
      )
    })
  })

  it('calls onGenerate with null templateName and freeform prompt when freeform selected', async () => {
    const onGenerate = vi.fn().mockResolvedValue({ jobId: 'job-2' })
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-002" format="pdf" onGenerate={onGenerate} />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'freeform' } })

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'Draft a demand letter for breach of contract.' } })

    fireEvent.click(screen.getByRole('button', { name: /generate/i }))

    await waitFor(() => {
      expect(onGenerate).toHaveBeenCalledWith(
        expect.objectContaining({
          matterId: 'matter-002',
          templateName: null,
          prompt: 'Draft a demand letter for breach of contract.',
          format: 'pdf',
        }),
      )
    })
  })

  it('includes the format prop in the generation request', async () => {
    const onGenerate = vi.fn().mockResolvedValue({ jobId: 'job-3' })
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-003" format="md" onGenerate={onGenerate} />)

    fireEvent.click(screen.getByRole('button', { name: /generate/i }))

    await waitFor(() => {
      expect(onGenerate).toHaveBeenCalledWith(
        expect.objectContaining({ format: 'md' }),
      )
    })
  })

  it('Generate button is disabled while generation is in progress', async () => {
    let resolveGenerate!: (val: { jobId: string }) => void
    const onGenerate = vi.fn().mockReturnValue(
      new Promise<{ jobId: string }>((res) => { resolveGenerate = res }),
    )
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={onGenerate} />)

    fireEvent.click(screen.getByRole('button', { name: /generate/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /generat/i })).toBeDisabled()
    })

    resolveGenerate({ jobId: 'job-done' })
  })

  it('shows default template selection as engagement_letter', async () => {
    const { DocumentGenPanel } = await import('./DocumentGenPanel')
    render(<DocumentGenPanel matterId="matter-1" format="docx" onGenerate={vi.fn()} />)

    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.value).toBe('engagement_letter')
  })
})
