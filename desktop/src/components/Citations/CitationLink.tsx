import type { Citation } from '../../types'

interface CitationLinkProps {
  citation: Citation
  index: number
  onCitationClick: (citation: Citation) => void
}

export function CitationLink({ citation, index, onCitationClick }: CitationLinkProps) {
  const pageInfo = citation.page !== null ? ` — p. ${citation.page}` : ''
  const titleText = `${citation.text_snippet}${pageInfo}`

  return (
    <button
      className="citation-link"
      title={titleText}
      onClick={() => onCitationClick(citation)}
      type="button"
    >
      [{index}]
    </button>
  )
}
