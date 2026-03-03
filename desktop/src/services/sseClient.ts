import type { Citation } from '../types'

type TokenCallback = (token: string) => void
type CitationsCallback = (citations: Citation[]) => void
type ErrorCallback = (error: Error) => void

export interface SSEClient {
  onToken: (cb: TokenCallback) => void
  onCitations: (cb: CitationsCallback) => void
  onError: (cb: ErrorCallback) => void
  connect: () => Promise<void>
  disconnect: () => void
}

interface TokenEvent {
  token: string
}

interface CitationsEvent {
  citations: Citation[]
}

export function createSSEClient(url: string, body: object, token: string): SSEClient {
  let tokenCallback: TokenCallback | null = null
  let citationsCallback: CitationsCallback | null = null
  let errorCallback: ErrorCallback | null = null
  let abortController: AbortController | null = null

  function parseSSELine(buffer: string): void {
    const lines = buffer.split('\n')
    let currentEvent = ''
    let currentData = ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        currentData = line.slice(6).trim()
      } else if (line === '' && currentEvent && currentData) {
        try {
          if (currentEvent === 'token') {
            const parsed = JSON.parse(currentData) as TokenEvent
            tokenCallback?.(parsed.token)
          } else if (currentEvent === 'citations') {
            const parsed = JSON.parse(currentData) as CitationsEvent
            citationsCallback?.(parsed.citations)
          }
        } catch {
          // Ignore parse errors for individual events
        }
        currentEvent = ''
        currentData = ''
      }
    }
  }

  return {
    onToken(cb: TokenCallback) {
      tokenCallback = cb
    },
    onCitations(cb: CitationsCallback) {
      citationsCallback = cb
    },
    onError(cb: ErrorCallback) {
      errorCallback = cb
    },
    async connect() {
      abortController = new AbortController()
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
            Accept: 'text/event-stream',
          },
          body: JSON.stringify(body),
          signal: abortController.signal,
        })

        if (!response.ok || !response.body) {
          throw new Error(`SSE connection failed: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          parseSSELine(chunk)
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return
        errorCallback?.(err instanceof Error ? err : new Error(String(err)))
      }
    },
    disconnect() {
      abortController?.abort()
    },
  }
}
