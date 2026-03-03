import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useAuthStore } from '../../stores/authStore';
// Mock Tauri plugin store
vi.mock('@tauri-apps/plugin-store', () => ({
    Store: vi.fn().mockImplementation(() => ({
        get: vi.fn().mockResolvedValue(null),
        set: vi.fn().mockResolvedValue(undefined),
        save: vi.fn().mockResolvedValue(undefined),
    })),
}));
// Mock tokenStorage to avoid Tauri dependency
vi.mock('../../services/tokenStorage', () => ({
    saveToken: vi.fn().mockResolvedValue(undefined),
    getToken: vi.fn().mockResolvedValue(null),
    clearToken: vi.fn().mockResolvedValue(undefined),
}));
// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;
describe('LoginPage (Task 5.3)', () => {
    const mockOnLoginSuccess = vi.fn();
    beforeEach(() => {
        mockFetch.mockClear();
        mockOnLoginSuccess.mockClear();
        useAuthStore.setState({ token: null, user: null });
    });
    it('renders email and password fields', async () => {
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });
    it('renders a submit button', async () => {
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });
    it('shows error message on invalid credentials', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 401,
            json: async () => ({ error: 'Invalid credentials' }),
        });
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        await userEvent.type(screen.getByLabelText(/email/i), 'bad@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword');
        fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
        await waitFor(() => {
            expect(screen.getByRole('alert')).toBeInTheDocument();
        });
    });
    it('calls onLoginSuccess on valid credentials', async () => {
        const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' };
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ token: 'valid-jwt', user: mockUser }),
        });
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'correctpassword');
        fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
        await waitFor(() => {
            expect(mockOnLoginSuccess).toHaveBeenCalled();
        });
    });
    it('stores JWT in auth store on successful login', async () => {
        const mockUser = { id: '1', email: 'test@example.com', name: 'Test User', role: 'attorney' };
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ token: 'valid-jwt', user: mockUser }),
        });
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'correctpassword');
        fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
        await waitFor(() => {
            const { token } = useAuthStore.getState();
            expect(token).toBe('valid-jwt');
        });
    });
    it('disables submit button while loading', async () => {
        let resolveRequest;
        mockFetch.mockReturnValueOnce(new Promise((resolve) => {
            resolveRequest = resolve;
        }));
        const { LoginPage } = await import('./LoginPage');
        render(_jsx(LoginPage, { onLoginSuccess: mockOnLoginSuccess }));
        await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
        await userEvent.type(screen.getByLabelText(/password/i), 'password');
        fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
        await waitFor(() => {
            expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
        });
        resolveRequest({
            ok: true,
            status: 200,
            json: async () => ({ token: 'jwt', user: { id: '1', email: 'test@example.com', name: 'Test', role: 'attorney' } }),
        });
    });
});
