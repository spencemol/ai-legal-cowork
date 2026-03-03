export type ExportFormat = 'docx' | 'pdf' | 'md'

interface ExportFormatSelectorProps {
  value: ExportFormat
  onChange: (format: ExportFormat) => void
}

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: 'docx', label: 'DOCX' },
  { value: 'pdf', label: 'PDF' },
  { value: 'md', label: 'Markdown' },
]

export function ExportFormatSelector({ value, onChange }: ExportFormatSelectorProps) {
  return (
    <div className="export-format-selector" role="group" aria-label="Export format">
      {FORMATS.map((fmt) => {
        const isSelected = fmt.value === value
        return (
          <button
            key={fmt.value}
            type="button"
            className={`format-btn${isSelected ? ' format-selected' : ''}`}
            aria-pressed={isSelected}
            onClick={() => onChange(fmt.value)}
          >
            {fmt.label}
          </button>
        )
      })}
    </div>
  )
}
