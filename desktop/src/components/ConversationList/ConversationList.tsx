import { useState, useEffect } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'
import type { Conversation } from '../../types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000'

export function ConversationList() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const token = useAuthStore((s) => s.token)
  const activeMatter = useChatStore((s) => s.activeMatter)
  const activeConversation = useChatStore((s) => s.activeConversation)
  const setActiveConversation = useChatStore((s) => s.setActiveConversation)

  const authHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  useEffect(() => {
    if (!activeMatter) return

    const fetchConversations = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/conversations?matterId=${activeMatter.id}`,
          { headers: authHeaders },
        )
        if (!response.ok) return
        const body = await response.json() as { data: Conversation[] }
        setConversations(body.data)
      } catch {
        // Silent fail for conversations load
      }
    }

    void fetchConversations()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeMatter, token])

  const handleNewChat = async () => {
    if (!activeMatter || isCreating) return
    setIsCreating(true)
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ matterId: activeMatter.id, title: 'New Chat' }),
      })
      if (!response.ok) return
      const body = await response.json() as { data: Conversation }
      const newConv = body.data
      setConversations((prev) => [newConv, ...prev])
      setActiveConversation(newConv)
    } catch {
      // Silent fail
    } finally {
      setIsCreating(false)
    }
  }

  const filteredConversations = searchQuery.trim()
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : conversations

  return (
    <div className="conversation-list">
      <div className="conversation-list-header">
        <button
          onClick={handleNewChat}
          disabled={isCreating || !activeMatter}
          type="button"
          className="new-chat-btn"
        >
          {isCreating ? 'Creating...' : 'New Chat'}
        </button>
      </div>

      <input
        type="text"
        placeholder="Search conversations..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="conversation-search"
      />

      <ul className="conversation-items">
        {filteredConversations.length === 0 && searchQuery.trim() ? (
          <li className="no-results">No conversations found</li>
        ) : (
          filteredConversations.map((conv) => (
            <li
              key={conv.id}
              className={`conversation-item ${activeConversation?.id === conv.id ? 'active' : ''}`}
              onClick={() => setActiveConversation(conv)}
            >
              {conv.title}
            </li>
          ))
        )}
      </ul>
    </div>
  )
}
