import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthStore } from '../stores/authStore';
// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;
describe('apiClient (Task 5.2)', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        useAuthStore.setState({ token: null, user: null });
    });
    afterEach(() => {
        vi.restoreAllMocks();
    });
    it('makes requests to base URL with path', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ status: 'ok' }),
        });
        const { apiRequest } = await import('./apiClient');
        await apiRequest('/health');
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/health'), expect.any(Object));
    });
    it('includes Authorization header when token is set', async () => {
        useAuthStore.setState({ token: 'test-token-123', user: null });
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ data: 'ok' }),
        });
        const { apiRequest } = await import('./apiClient');
        await apiRequest('/health');
        expect(mockFetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({
            headers: expect.objectContaining({
                Authorization: 'Bearer test-token-123',
            }),
        }));
    });
    it('does not include Authorization header when no token', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ data: 'ok' }),
        });
        const { apiRequest } = await import('./apiClient');
        await apiRequest('/health');
        const callArgs = mockFetch.mock.calls[0];
        const headers = callArgs[1]?.headers ?? {};
        expect(headers).not.toHaveProperty('Authorization');
    });
    it('calls logout on 401 response', async () => {
        useAuthStore.setState({ token: 'expired-token', user: { id: '1', email: 'a@b.com', name: 'A', role: 'attorney' } });
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 401,
            json: async () => ({ error: 'Unauthorized' }),
        });
        const { apiRequest } = await import('./apiClient');
        await expect(apiRequest('/protected')).rejects.toThrow();
        const { token } = useAuthStore.getState();
        expect(token).toBeNull();
    });
    it('throws on non-OK responses (not 401)', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ error: 'Server error' }),
        });
        const { apiRequest } = await import('./apiClient');
        await expect(apiRequest('/data')).rejects.toThrow();
    });
    it('returns parsed JSON on success', async () => {
        const responseData = { id: '1', title: 'Test Matter' };
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => responseData,
        });
        const { apiRequest } = await import('./apiClient');
        const result = await apiRequest('/matters/1');
        expect(result).toEqual(responseData);
    });
});
