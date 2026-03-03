import { useState } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled: boolean
  placeholder?: string
}

export function ChatInput({ onSend, disabled, placeholder = 'Type a message...' }: ChatInputProps) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-input">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={3}
      />
      <button onClick={handleSend} disabled={disabled} type="button">
        Send
      </button>
    </div>
  )
}
