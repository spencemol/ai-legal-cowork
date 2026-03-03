import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from './stores/authStore';
import App from './App';
vi.mock('@tauri-apps/plugin-store', () => ({
    Store: vi.fn().mockImplementation(() => ({
        get: vi.fn().mockResolvedValue(null),
        set: vi.fn().mockResolvedValue(undefined),
        save: vi.fn().mockResolvedValue(undefined),
    })),
}));
vi.mock('./services/tokenStorage', () => ({
    saveToken: vi.fn().mockResolvedValue(undefined),
    getToken: vi.fn().mockResolvedValue(null),
    clearToken: vi.fn().mockResolvedValue(undefined),
}));
const mockFetch = vi.fn();
global.fetch = mockFetch;
describe('App', () => {
    beforeEach(() => {
        useAuthStore.setState({ token: null, user: null });
        mockFetch.mockClear();
    });
    it('renders login page when not authenticated', () => {
        render(_jsx(App, {}));
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });
    it('renders main view when authenticated', () => {
        mockFetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: async () => ({ data: [] }),
        });
        useAuthStore.setState({
            token: 'valid-token',
            user: { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' },
        });
        render(_jsx(App, {}));
        expect(screen.getByText('Legal AI Tool')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    });
});
