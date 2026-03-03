import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../../stores/authStore'
import type { Citation } from '../../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000'

interface DocumentData {
  id: string
  title: string
  content: string
  mimeType: string
}

interface DocumentViewerProps {
  citation: Citation | null
  onClose: () => void
}

export function DocumentViewer({ citation, onClose }: DocumentViewerProps) {
  const [document, setDocument] = useState<DocumentData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const token = useAuthStore((s) => s.token)
  const highlightRef = useRef<HTMLSpanElement | null>(null)

  useEffect(() => {
    if (!citation) {
      setDocument(null)
      setError(null)
      return
    }

    const fetchDocument = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch(`${API_BASE_URL}/documents/${citation.doc_id}`, { headers })

        if (!response.ok) {
          throw new Error('Failed to load document')
        }

        const body = await response.json() as { data: DocumentData }
        setDocument(body.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading document')
      } finally {
        setIsLoading(false)
      }
    }

    void fetchDocument()
  }, [citation, token])

  // Scroll highlighted chunk into view after render (guarded for jsdom compatibility)
  useEffect(() => {
    if (highlightRef.current && typeof highlightRef.current.scrollIntoView === 'function') {
      highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [document])

  if (!citation) return null

  if (isLoading) {
    return (
      <div className="document-viewer">
        <div className="document-viewer-header">
          <button onClick={onClose} type="button">Close</button>
        </div>
        <div>Loading document...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-viewer">
        <div className="document-viewer-header">
          <button onClick={onClose} type="button">Close</button>
        </div>
        <div className="error">Error: {error}</div>
      </div>
    )
  }

  if (!document) return null

  // Render content with highlighted snippet
  const renderContent = () => {
    if (!citation.text_snippet || !document.content.includes(citation.text_snippet)) {
      return <pre className="document-content">{document.content}</pre>
    }

    const snippetIndex = document.content.indexOf(citation.text_snippet)
    const before = document.content.slice(0, snippetIndex)
    const snippet = document.content.slice(snippetIndex, snippetIndex + citation.text_snippet.length)
    const after = document.content.slice(snippetIndex + citation.text_snippet.length)

    return (
      <pre className="document-content">
        {before}
        <span className="highlighted-chunk" ref={highlightRef}>
          {snippet}
        </span>
        {after}
      </pre>
    )
  }

  return (
    <div className="document-viewer">
      <div className="document-viewer-header">
        <h3>{document.title}</h3>
        <button onClick={onClose} type="button">Close</button>
      </div>
      <div className="document-viewer-body">
        {renderContent()}
      </div>
    </div>
  )
}
