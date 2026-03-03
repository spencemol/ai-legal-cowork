import { useAuthStore } from '../stores/authStore';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
export async function apiRequest(path, options = {}) {
    const { token } = useAuthStore.getState();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });
    if (response.status === 401) {
        useAuthStore.getState().logout();
        throw new Error('Unauthorized: session expired');
    }
    if (!response.ok) {
        const body = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(body.error ?? `Request failed with status ${response.status}`);
    }
    return response.json();
}
export function getAgentsBaseUrl() {
    return import.meta.env.VITE_AGENTS_URL ?? 'http://localhost:8000';
}
