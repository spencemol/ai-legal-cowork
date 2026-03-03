import { useState, useCallback } from 'react'
import { showSaveDialog, writeTextFile, writeBinaryFile } from '../services/tauriFs'

export type DocumentFormat = 'docx' | 'pdf' | 'md'

interface UseDocumentDownloadReturn {
  isDownloading: boolean
  error: string | null
  downloadDocument: (content: string, filename: string, format: DocumentFormat) => Promise<void>
}

/**
 * Hook that wraps the Tauri save-dialog + file-write workflow.
 * Tests mock `../services/tauriFs` to avoid actual Tauri plugin calls.
 */
export function useDocumentDownload(): UseDocumentDownloadReturn {
  const [isDownloading, setIsDownloading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const downloadDocument = useCallback(
    async (content: string, filename: string, format: DocumentFormat): Promise<void> => {
      setIsDownloading(true)
      setError(null)
      try {
        const chosenPath = await showSaveDialog(filename)
        if (chosenPath === null) {
          // User cancelled the dialog
          return
        }

        if (format === 'md') {
          await writeTextFile(chosenPath, content)
        } else {
          // docx and pdf come as base64-encoded binary from the backend
          await writeBinaryFile(chosenPath, content)
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        setError(message)
      } finally {
        setIsDownloading(false)
      }
    },
    [],
  )

  return { isDownloading, error, downloadDocument }
}
