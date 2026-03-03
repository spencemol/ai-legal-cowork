import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
import { createSSEClient } from '../../services/sseClient';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { CitationLink } from '../Citations/CitationLink';
import { DocumentViewer } from '../DocumentViewer/DocumentViewer';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
const AGENTS_BASE_URL = import.meta.env.VITE_AGENTS_URL ?? 'http://localhost:8000';
export function ChatWindow() {
    const [isSending, setIsSending] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [selectedCitation, setSelectedCitation] = useState(null);
    const messagesEndRef = useRef(null);
    const sseClientRef = useRef(null);
    const token = useAuthStore((s) => s.token);
    const activeConversation = useChatStore((s) => s.activeConversation);
    const messages = useChatStore((s) => s.messages);
    const appendMessage = useChatStore((s) => s.appendMessage);
    const appendToken = useChatStore((s) => s.appendToken);
    const setMessages = useChatStore((s) => s.setMessages);
    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);
    // Clean up SSE on unmount
    useEffect(() => {
        return () => {
            sseClientRef.current?.disconnect();
        };
    }, []);
    const handleSend = async (text) => {
        if (!activeConversation || !token)
            return;
        const userMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: text,
        };
        appendMessage(userMessage);
        setIsSending(true);
        try {
            // Save user message to API
            const authHeaders = {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            };
            await fetch(`${API_BASE_URL}/conversations/${activeConversation.id}/messages`, {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify({ role: 'user', content: text }),
            });
            // Create a placeholder for the assistant streaming response
            const assistantPlaceholder = {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: '',
            };
            appendMessage(assistantPlaceholder);
            setIsStreaming(true);
            // Connect SSE for streaming response
            const sseClient = createSSEClient(`${AGENTS_BASE_URL}/chat`, { conversationId: activeConversation.id, message: text, matterId: activeConversation.matterId }, token);
            sseClientRef.current = sseClient;
            sseClient.onToken((tokenChunk) => {
                appendToken(activeConversation.id, tokenChunk);
            });
            sseClient.onCitations((citations) => {
                // Update the last assistant message with citations
                const currentMessages = useChatStore.getState().messages;
                const lastMsg = currentMessages[currentMessages.length - 1];
                if (lastMsg?.role === 'assistant') {
                    const updated = [...currentMessages];
                    updated[updated.length - 1] = { ...lastMsg, citations };
                    setMessages(updated);
                }
            });
            sseClient.onError(() => {
                setIsStreaming(false);
            });
            await sseClient.connect();
            setIsStreaming(false);
        }
        finally {
            setIsSending(false);
        }
    };
    if (!activeConversation) {
        return (_jsx("div", { className: "chat-window chat-window-empty", children: _jsx("p", { children: "Select or create a conversation to start chatting" }) }));
    }
    return (_jsxs("div", { className: "chat-window", children: [_jsxs("div", { className: "chat-messages", children: [messages.map((msg, idx) => (_jsxs("div", { children: [_jsx(ChatMessage, { message: msg, isStreaming: isStreaming && idx === messages.length - 1 && msg.role === 'assistant', onCitationClick: setSelectedCitation }), msg.citations && msg.citations.length > 0 && (_jsx("div", { className: "inline-citations", children: msg.citations.map((cit, citIdx) => (_jsx(CitationLink, { citation: cit, index: citIdx + 1, onCitationClick: setSelectedCitation }, cit.chunk_id))) }))] }, msg.id))), _jsx("div", { ref: messagesEndRef })] }), _jsx(ChatInput, { onSend: handleSend, disabled: isSending || isStreaming }), selectedCitation && (_jsx(DocumentViewer, { citation: selectedCitation, onClose: () => setSelectedCitation(null) }))] }));
}
