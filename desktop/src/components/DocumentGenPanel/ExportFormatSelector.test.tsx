/**
 * Phase 8 Task 8.4 — ExportFormatSelector component tests.
 *
 * Verifies:
 * - Renders three toggle buttons: DOCX, PDF, Markdown
 * - Default selected format is DOCX
 * - Clicking a button calls onChange with the selected format
 * - Only one format is marked as selected at a time (aria-pressed / selected class)
 * - Selected button has the "selected" CSS class
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

describe('ExportFormatSelector (Phase 8 Task 8.4)', () => {
  it('renders DOCX, PDF, and Markdown buttons', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: /docx/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pdf/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /markdown/i })).toBeInTheDocument()
  })

  it('DOCX button is marked as selected when value is "docx"', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={vi.fn()} />)

    const docxBtn = screen.getByRole('button', { name: /docx/i })
    expect(docxBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('PDF button is not selected when value is "docx"', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={vi.fn()} />)

    const pdfBtn = screen.getByRole('button', { name: /pdf/i })
    expect(pdfBtn).toHaveAttribute('aria-pressed', 'false')
  })

  it('clicking PDF calls onChange with "pdf"', async () => {
    const onChange = vi.fn()
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={onChange} />)

    fireEvent.click(screen.getByRole('button', { name: /pdf/i }))
    expect(onChange).toHaveBeenCalledWith('pdf')
  })

  it('clicking Markdown calls onChange with "md"', async () => {
    const onChange = vi.fn()
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={onChange} />)

    fireEvent.click(screen.getByRole('button', { name: /markdown/i }))
    expect(onChange).toHaveBeenCalledWith('md')
  })

  it('clicking DOCX calls onChange with "docx"', async () => {
    const onChange = vi.fn()
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="pdf" onChange={onChange} />)

    fireEvent.click(screen.getByRole('button', { name: /docx/i }))
    expect(onChange).toHaveBeenCalledWith('docx')
  })

  it('Markdown button has aria-pressed true when value is "md"', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="md" onChange={vi.fn()} />)

    const mdBtn = screen.getByRole('button', { name: /markdown/i })
    expect(mdBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('selected button has "format-selected" CSS class', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    const { container } = render(<ExportFormatSelector value="pdf" onChange={vi.fn()} />)

    const pdfBtn = screen.getByRole('button', { name: /pdf/i })
    expect(pdfBtn).toHaveClass('format-selected')

    const docxBtn = screen.getByRole('button', { name: /docx/i })
    expect(docxBtn).not.toHaveClass('format-selected')

    // suppress unused var warning
    void container
  })

  it('exactly one button is selected at a time', async () => {
    const { ExportFormatSelector } = await import('./ExportFormatSelector')
    render(<ExportFormatSelector value="docx" onChange={vi.fn()} />)

    const pressedBtns = screen.getAllByRole('button').filter(
      (btn) => btn.getAttribute('aria-pressed') === 'true',
    )
    expect(pressedBtns).toHaveLength(1)
  })
})
