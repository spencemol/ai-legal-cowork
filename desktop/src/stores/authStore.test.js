import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';
const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' };
const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';
describe('authStore (Task 5.1)', () => {
    beforeEach(() => {
        // Reset store state between tests
        useAuthStore.setState({ token: null, user: null });
    });
    it('initializes with null token and user', () => {
        const { token, user } = useAuthStore.getState();
        expect(token).toBeNull();
        expect(user).toBeNull();
    });
    it('login action sets token and user', () => {
        useAuthStore.getState().login(mockToken, mockUser);
        const { token, user } = useAuthStore.getState();
        expect(token).toBe(mockToken);
        expect(user).toEqual(mockUser);
    });
    it('logout action clears token and user', () => {
        useAuthStore.setState({ token: mockToken, user: mockUser });
        useAuthStore.getState().logout();
        const { token, user } = useAuthStore.getState();
        expect(token).toBeNull();
        expect(user).toBeNull();
    });
    it('isAuthenticated returns true when token is set', () => {
        useAuthStore.setState({ token: mockToken, user: mockUser });
        expect(useAuthStore.getState().isAuthenticated()).toBe(true);
    });
    it('isAuthenticated returns false when token is null', () => {
        expect(useAuthStore.getState().isAuthenticated()).toBe(false);
    });
});
