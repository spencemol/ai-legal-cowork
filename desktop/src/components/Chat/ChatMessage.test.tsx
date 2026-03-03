import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { Message } from '../../types'

describe('ChatMessage (Task 5.8)', () => {
  it('renders user message with correct role label', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = { id: '1', role: 'user', content: 'What is the law?' }
    render(<ChatMessage message={message} />)

    expect(screen.getByText('What is the law?')).toBeInTheDocument()
    expect(screen.getByText(/you/i)).toBeInTheDocument()
  })

  it('renders assistant message with correct role label', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = { id: '2', role: 'assistant', content: 'The law states...' }
    render(<ChatMessage message={message} />)

    expect(screen.getByText('The law states...')).toBeInTheDocument()
    expect(screen.getByText(/assistant/i)).toBeInTheDocument()
  })

  it('renders citations when present', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = {
      id: '3',
      role: 'assistant',
      content: 'Based on the statute...',
      citations: [
        { doc_id: 'doc1', chunk_id: 'c1', text_snippet: 'Statute text here', page: 5 },
      ],
    }
    render(<ChatMessage message={message} />)

    expect(screen.getByText('Based on the statute...')).toBeInTheDocument()
  })

  it('shows streaming indicator when isStreaming is true', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = { id: '4', role: 'assistant', content: 'Thinking...' }
    render(<ChatMessage message={message} isStreaming={true} />)

    expect(screen.getByText('Thinking...')).toBeInTheDocument()
    // Streaming indicator (cursor/animation) should be present
    const streamingEl = document.querySelector('.streaming-cursor')
    expect(streamingEl).toBeTruthy()
  })

  it('applies user message styling class', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = { id: '5', role: 'user', content: 'My question' }
    const { container } = render(<ChatMessage message={message} />)

    expect(container.querySelector('.message-user')).toBeTruthy()
  })

  it('applies assistant message styling class', async () => {
    const { ChatMessage } = await import('./ChatMessage')
    const message: Message = { id: '6', role: 'assistant', content: 'My answer' }
    const { container } = render(<ChatMessage message={message} />)

    expect(container.querySelector('.message-assistant')).toBeTruthy()
  })
})
