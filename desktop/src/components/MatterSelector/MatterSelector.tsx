import { useState, useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'
import type { Matter } from '../../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000'

export function MatterSelector() {
  const [matters, setMatters] = useState<Matter[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const token = useAuthStore((s) => s.token)
  const activeMatter = useChatStore((s) => s.activeMatter)
  const setActiveMatter = useChatStore((s) => s.setActiveMatter)

  useEffect(() => {
    const fetchMatters = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch(`${API_BASE_URL}/matters`, { headers })

        if (!response.ok) {
          throw new Error('Failed to load matters')
        }

        const body = await response.json() as { data: Matter[] }
        setMatters(body.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading matters')
      } finally {
        setIsLoading(false)
      }
    }

    void fetchMatters()
  }, [token])

  if (isLoading) {
    return <div className="matter-selector">Loading matters...</div>
  }

  if (error) {
    return <div className="matter-selector error">Error: {error}</div>
  }

  return (
    <div className="matter-selector">
      <h3>Your Matters</h3>
      <ul role="listbox">
        {matters.map((matter) => (
          <li
            key={matter.id}
            role="option"
            aria-selected={activeMatter?.id === matter.id}
            onClick={() => setActiveMatter(matter)}
            style={{ cursor: 'pointer', fontWeight: activeMatter?.id === matter.id ? 'bold' : 'normal' }}
          >
            {matter.title}
            <span className="case-number"> ({matter.caseNumber})</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
