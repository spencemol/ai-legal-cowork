import { describe, it, expect, vi, beforeEach } from 'vitest';
// Mock fetch for SSE tests
const mockFetch = vi.fn();
global.fetch = mockFetch;
function makeSSEStream(events) {
    const encoder = new TextEncoder();
    return new ReadableStream({
        start(controller) {
            for (const event of events) {
                controller.enqueue(encoder.encode(event));
            }
            controller.close();
        },
    });
}
describe('sseClient (Task 5.6)', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });
    it('exports createSSEClient function', async () => {
        const { createSSEClient } = await import('./sseClient');
        expect(typeof createSSEClient).toBe('function');
    });
    it('creates a client with connect, disconnect, onToken, onCitations, onError methods', async () => {
        const { createSSEClient } = await import('./sseClient');
        const client = createSSEClient('http://localhost:8000/chat', { message: 'hello' }, 'token');
        expect(typeof client.connect).toBe('function');
        expect(typeof client.disconnect).toBe('function');
        expect(typeof client.onToken).toBe('function');
        expect(typeof client.onCitations).toBe('function');
        expect(typeof client.onError).toBe('function');
    });
    it('calls fetch with POST method and Authorization header', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            body: makeSSEStream([]),
        });
        const { createSSEClient } = await import('./sseClient');
        const client = createSSEClient('http://localhost:8000/chat', { message: 'hello' }, 'test-token');
        await client.connect();
        expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/chat', expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
                Authorization: 'Bearer test-token',
            }),
        }));
    });
    it('invokes onToken callback for token SSE events', async () => {
        const sseData = [
            'event: token\ndata: {"token":"Hello"}\n\n',
            'event: token\ndata: {"token":" World"}\n\n',
        ];
        mockFetch.mockResolvedValueOnce({
            ok: true,
            body: makeSSEStream(sseData),
        });
        const { createSSEClient } = await import('./sseClient');
        const tokenCallback = vi.fn();
        const client = createSSEClient('http://localhost:8000/chat', { message: 'hi' }, 'token');
        client.onToken(tokenCallback);
        await client.connect();
        expect(tokenCallback).toHaveBeenCalledWith('Hello');
        expect(tokenCallback).toHaveBeenCalledWith(' World');
    });
    it('invokes onCitations callback for citations SSE events', async () => {
        const citations = [
            { doc_id: 'doc1', chunk_id: 'c1', text_snippet: 'Some legal text', page: 1 },
        ];
        const sseData = [`event: citations\ndata: ${JSON.stringify({ citations })}\n\n`];
        mockFetch.mockResolvedValueOnce({
            ok: true,
            body: makeSSEStream(sseData),
        });
        const { createSSEClient } = await import('./sseClient');
        const citationsCallback = vi.fn();
        const client = createSSEClient('http://localhost:8000/chat', { message: 'research' }, 'token');
        client.onCitations(citationsCallback);
        await client.connect();
        expect(citationsCallback).toHaveBeenCalledWith(citations);
    });
    it('invokes onError callback when fetch fails', async () => {
        mockFetch.mockRejectedValueOnce(new Error('Network error'));
        const { createSSEClient } = await import('./sseClient');
        const errorCallback = vi.fn();
        const client = createSSEClient('http://localhost:8000/chat', { message: 'test' }, 'token');
        client.onError(errorCallback);
        await client.connect();
        expect(errorCallback).toHaveBeenCalled();
    });
});
