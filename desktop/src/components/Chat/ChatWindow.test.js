import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
const mockFetch = vi.fn();
global.fetch = mockFetch;
vi.mock('../../services/sseClient', () => ({
    createSSEClient: vi.fn().mockReturnValue({
        onToken: vi.fn(),
        onCitations: vi.fn(),
        onError: vi.fn(),
        connect: vi.fn().mockResolvedValue(undefined),
        disconnect: vi.fn(),
    }),
}));
const mockMatter = { id: 'm1', title: 'Smith v. Jones', caseNumber: '2024-001', status: 'active' };
const mockConversation = { id: 'conv1', title: 'Chat 1', matterId: 'm1', createdAt: '2024-01-01T00:00:00Z' };
describe('ChatWindow (Task 5.8 integration)', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        useAuthStore.setState({ token: 'test-token', user: { id: '1', email: 'a@b.com', name: 'A', role: 'attorney' } });
        useChatStore.setState({
            activeMatter: mockMatter,
            activeConversation: mockConversation,
            messages: [],
            conversations: [],
            searchQuery: '',
        });
    });
    it('renders chat input', async () => {
        const { ChatWindow } = await import('./ChatWindow');
        render(_jsx(ChatWindow, {}));
        expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
    it('renders send button', async () => {
        const { ChatWindow } = await import('./ChatWindow');
        render(_jsx(ChatWindow, {}));
        expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });
    it('shows message in chat after sending', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 201,
            json: async () => ({ data: { id: 'msg1', role: 'user', content: 'What is the law?' } }),
        });
        const { ChatWindow } = await import('./ChatWindow');
        render(_jsx(ChatWindow, {}));
        const textarea = screen.getByRole('textbox');
        fireEvent.change(textarea, { target: { value: 'What is the law?' } });
        fireEvent.click(screen.getByRole('button', { name: /send/i }));
        await waitFor(() => {
            expect(screen.getByText('What is the law?')).toBeInTheDocument();
        });
    });
    it('shows placeholder when no active conversation', async () => {
        useChatStore.setState({
            activeMatter: mockMatter,
            activeConversation: null,
            messages: [],
            conversations: [],
            searchQuery: '',
        });
        const { ChatWindow } = await import('./ChatWindow');
        render(_jsx(ChatWindow, {}));
        expect(screen.getByText(/select or create a conversation/i)).toBeInTheDocument();
    });
    it('renders existing messages from store', async () => {
        useChatStore.setState({
            activeMatter: mockMatter,
            activeConversation: mockConversation,
            messages: [
                { id: 'm1', role: 'user', content: 'Previous message' },
                { id: 'm2', role: 'assistant', content: 'Previous answer' },
            ],
            conversations: [],
            searchQuery: '',
        });
        const { ChatWindow } = await import('./ChatWindow');
        render(_jsx(ChatWindow, {}));
        expect(screen.getByText('Previous message')).toBeInTheDocument();
        expect(screen.getByText('Previous answer')).toBeInTheDocument();
    });
});
