import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
export function ConversationList() {
    const [conversations, setConversations] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const token = useAuthStore((s) => s.token);
    const activeMatter = useChatStore((s) => s.activeMatter);
    const activeConversation = useChatStore((s) => s.activeConversation);
    const setActiveConversation = useChatStore((s) => s.setActiveConversation);
    const authHeaders = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    useEffect(() => {
        if (!activeMatter)
            return;
        const fetchConversations = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/conversations?matterId=${activeMatter.id}`, { headers: authHeaders });
                if (!response.ok)
                    return;
                const body = await response.json();
                setConversations(body.data);
            }
            catch {
                // Silent fail for conversations load
            }
        };
        void fetchConversations();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeMatter, token]);
    const handleNewChat = async () => {
        if (!activeMatter || isCreating)
            return;
        setIsCreating(true);
        try {
            const response = await fetch(`${API_BASE_URL}/conversations`, {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({ matterId: activeMatter.id, title: 'New Chat' }),
            });
            if (!response.ok)
                return;
            const body = await response.json();
            const newConv = body.data;
            setConversations((prev) => [newConv, ...prev]);
            setActiveConversation(newConv);
        }
        catch {
            // Silent fail
        }
        finally {
            setIsCreating(false);
        }
    };
    const filteredConversations = searchQuery.trim()
        ? conversations.filter((c) => c.title.toLowerCase().includes(searchQuery.toLowerCase()))
        : conversations;
    return (_jsxs("div", { className: "conversation-list", children: [_jsx("div", { className: "conversation-list-header", children: _jsx("button", { onClick: handleNewChat, disabled: isCreating || !activeMatter, type: "button", className: "new-chat-btn", children: isCreating ? 'Creating...' : 'New Chat' }) }), _jsx("input", { type: "text", placeholder: "Search conversations...", value: searchQuery, onChange: (e) => setSearchQuery(e.target.value), className: "conversation-search" }), _jsx("ul", { className: "conversation-items", children: filteredConversations.length === 0 && searchQuery.trim() ? (_jsx("li", { className: "no-results", children: "No conversations found" })) : (filteredConversations.map((conv) => (_jsx("li", { className: `conversation-item ${activeConversation?.id === conv.id ? 'active' : ''}`, onClick: () => setActiveConversation(conv), children: conv.title }, conv.id)))) })] }));
}
