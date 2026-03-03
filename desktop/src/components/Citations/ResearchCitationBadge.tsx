import type { Citation } from '../../types'

interface ResearchCitationBadgeProps {
  citation: Citation
  index: number
  onCitationClick: (citation: Citation) => void
}

type SourceType = 'firm' | 'web' | 'legal_db'

function resolveSourceType(citation: Citation): SourceType {
  if (citation.source === 'westlaw' || citation.source === 'lexisnexis') {
    return 'legal_db'
  }
  if (citation.source === 'web') {
    return 'web'
  }
  // 'firm' or absent → treat as internal
  return 'firm'
}

interface BadgeConfig {
  label: string
  cssClass: string
}

const BADGE_CONFIG: Record<SourceType, BadgeConfig> = {
  firm: { label: 'Internal', cssClass: 'badge-internal' },
  web: { label: 'Web', cssClass: 'badge-web' },
  legal_db: { label: 'Legal DB', cssClass: 'badge-legal-db' },
}

function getLinkText(citation: Citation, index: number, sourceType: SourceType): string {
  if (sourceType === 'web') {
    return citation.url ?? citation.title ?? `[${index}]`
  }
  if (sourceType === 'legal_db') {
    return citation.citation ?? citation.title ?? `[${index}]`
  }
  return `[${index}]`
}

export function ResearchCitationBadge({
  citation,
  index,
  onCitationClick,
}: ResearchCitationBadgeProps) {
  const sourceType = resolveSourceType(citation)
  const { label, cssClass } = BADGE_CONFIG[sourceType]
  const linkText = getLinkText(citation, index, sourceType)
  const pageInfo = citation.page != null ? ` — p. ${citation.page}` : ''
  const tooltipText = `${citation.text_snippet}${pageInfo}`

  return (
    <span className="research-citation-badge">
      <span className={`citation-badge ${cssClass}`}>{label}</span>
      <button
        className="citation-link"
        title={tooltipText}
        onClick={() => onCitationClick(citation)}
        type="button"
      >
        {linkText}
      </button>
    </span>
  )
}
