/**
 * Phase 8 Task 8.3 — useDocumentDownload hook tests.
 *
 * Verifies:
 * - downloadDocument calls showSaveDialog with the suggested filename
 * - If save dialog returns a path, writeTextFile is called with content
 * - If save dialog returns null (user cancelled), writeTextFile is not called
 * - Binary format (docx) uses writeBinaryFile
 * - Hook exposes isDownloading state (false initially, true during download)
 * - Hook exposes error state (null initially)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mock the tauriFs adapter
// ---------------------------------------------------------------------------

const mockShowSaveDialog = vi.fn()
const mockWriteTextFile = vi.fn()
const mockWriteBinaryFile = vi.fn()

vi.mock('../services/tauriFs', () => ({
  showSaveDialog: mockShowSaveDialog,
  writeTextFile: mockWriteTextFile,
  writeBinaryFile: mockWriteBinaryFile,
}))

describe('useDocumentDownload (Phase 8 Task 8.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockShowSaveDialog.mockResolvedValue('/chosen/path/output.md')
    mockWriteTextFile.mockResolvedValue(undefined)
    mockWriteBinaryFile.mockResolvedValue(undefined)
  })

  it('isDownloading starts as false', async () => {
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())
    expect(result.current.isDownloading).toBe(false)
  })

  it('error starts as null', async () => {
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())
    expect(result.current.error).toBeNull()
  })

  it('calls showSaveDialog with the suggested filename', async () => {
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    await act(async () => {
      await result.current.downloadDocument('Hello world', 'report.md', 'md')
    })

    expect(mockShowSaveDialog).toHaveBeenCalledWith('report.md')
  })

  it('calls writeTextFile with the chosen path and content for md format', async () => {
    mockShowSaveDialog.mockResolvedValue('/docs/report.md')
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    await act(async () => {
      await result.current.downloadDocument('# My Document', 'report.md', 'md')
    })

    expect(mockWriteTextFile).toHaveBeenCalledWith('/docs/report.md', '# My Document')
  })

  it('does not call writeTextFile when user cancels save dialog (null path)', async () => {
    mockShowSaveDialog.mockResolvedValue(null)
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    await act(async () => {
      await result.current.downloadDocument('content', 'doc.md', 'md')
    })

    expect(mockWriteTextFile).not.toHaveBeenCalled()
    expect(mockWriteBinaryFile).not.toHaveBeenCalled()
  })

  it('calls writeBinaryFile for docx format', async () => {
    mockShowSaveDialog.mockResolvedValue('/docs/contract.docx')
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    const base64Content = btoa('fake-docx-bytes')
    await act(async () => {
      await result.current.downloadDocument(base64Content, 'contract.docx', 'docx')
    })

    expect(mockWriteBinaryFile).toHaveBeenCalledWith('/docs/contract.docx', base64Content)
    expect(mockWriteTextFile).not.toHaveBeenCalled()
  })

  it('calls writeBinaryFile for pdf format', async () => {
    mockShowSaveDialog.mockResolvedValue('/docs/report.pdf')
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    const base64Content = btoa('fake-pdf-bytes')
    await act(async () => {
      await result.current.downloadDocument(base64Content, 'report.pdf', 'pdf')
    })

    expect(mockWriteBinaryFile).toHaveBeenCalledWith('/docs/report.pdf', base64Content)
  })

  it('isDownloading is false after successful download', async () => {
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    await act(async () => {
      await result.current.downloadDocument('content', 'doc.md', 'md')
    })

    expect(result.current.isDownloading).toBe(false)
  })

  it('sets error and clears isDownloading when writeTextFile throws', async () => {
    mockShowSaveDialog.mockResolvedValue('/docs/out.md')
    mockWriteTextFile.mockRejectedValue(new Error('Disk full'))
    const { useDocumentDownload } = await import('./useDocumentDownload')
    const { result } = renderHook(() => useDocumentDownload())

    await act(async () => {
      await result.current.downloadDocument('content', 'out.md', 'md')
    })

    expect(result.current.error).toBe('Disk full')
    expect(result.current.isDownloading).toBe(false)
  })
})
