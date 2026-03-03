import type { Message, Citation } from '../../types'

interface ChatMessageProps {
  message: Message
  isStreaming?: boolean
  onCitationClick?: (citation: Citation) => void
}

export function ChatMessage({ message, isStreaming = false, onCitationClick }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-role">
        {isUser ? 'You' : 'Assistant'}
      </div>
      <div className="message-content">
        {message.content}
        {isStreaming && <span className="streaming-cursor">▋</span>}
      </div>
      {message.citations && message.citations.length > 0 && (
        <div className="message-citations">
          {message.citations.map((citation, index) => (
            <button
              key={citation.chunk_id}
              className="citation-ref"
              onClick={() => onCitationClick?.(citation)}
              type="button"
            >
              [{index + 1}]
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
