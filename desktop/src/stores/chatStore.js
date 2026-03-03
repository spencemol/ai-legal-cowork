import { create } from 'zustand';
export const useChatStore = create()((set) => ({
    activeMatter: null,
    activeConversation: null,
    messages: [],
    conversations: [],
    searchQuery: '',
    setActiveMatter: (matter) => set({ activeMatter: matter }),
    setActiveConversation: (conversation) => set({ activeConversation: conversation, messages: [] }),
    setMessages: (messages) => set({ messages }),
    appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
    appendToken: (conversationId, token) => set((state) => {
        const msgs = [...state.messages];
        // Find the last assistant message for this conversation and append token
        const lastIdx = msgs.length - 1;
        if (lastIdx >= 0 && msgs[lastIdx].role === 'assistant') {
            msgs[lastIdx] = { ...msgs[lastIdx], content: msgs[lastIdx].content + token };
            return { messages: msgs };
        }
        // Create a new streaming assistant message
        return {
            messages: [
                ...msgs,
                { id: `stream-${conversationId}-${Date.now()}`, role: 'assistant', content: token },
            ],
        };
    }),
    setConversations: (conversations) => set({ conversations }),
    setSearchQuery: (query) => set({ searchQuery: query }),
}));
