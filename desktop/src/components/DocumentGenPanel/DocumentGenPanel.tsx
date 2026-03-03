import { useState } from 'react'
import type { ExportFormat } from './ExportFormatSelector'

export interface GenerationRequest {
  matterId: string
  templateName: string | null
  prompt?: string
  context?: Record<string, string>
  format: ExportFormat
}

interface DocumentGenPanelProps {
  matterId: string
  format: ExportFormat
  onGenerate: (req: GenerationRequest) => Promise<{ jobId: string }>
}

const TEMPLATES = [
  { value: 'engagement_letter', label: 'Engagement Letter' },
  { value: 'nda', label: 'Non-Disclosure Agreement' },
  { value: 'motion', label: 'Motion' },
  { value: 'freeform', label: 'Freeform (custom prompt)' },
]

export function DocumentGenPanel({ matterId, format, onGenerate }: DocumentGenPanelProps) {
  const [template, setTemplate] = useState<string>('engagement_letter')
  const [freeformPrompt, setFreeformPrompt] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState<boolean>(false)

  const isFreeform = template === 'freeform'

  async function handleGenerate() {
    setIsGenerating(true)
    try {
      const req: GenerationRequest = {
        matterId,
        templateName: isFreeform ? null : template,
        format,
        ...(isFreeform ? { prompt: freeformPrompt } : {}),
      }
      await onGenerate(req)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="document-gen-panel">
      <label htmlFor="doc-template-select" className="doc-gen-label">
        Template
      </label>
      <select
        id="doc-template-select"
        value={template}
        onChange={(e) => setTemplate(e.target.value)}
      >
        {TEMPLATES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>

      {isFreeform && (
        <textarea
          className="freeform-prompt"
          placeholder="Describe the document you need..."
          value={freeformPrompt}
          onChange={(e) => setFreeformPrompt(e.target.value)}
          rows={4}
        />
      )}

      <button
        type="button"
        className="generate-btn"
        onClick={handleGenerate}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate'}
      </button>
    </div>
  )
}
