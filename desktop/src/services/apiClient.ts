import { useAuthStore } from '../stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000'

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { token } = useAuthStore.getState()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    useAuthStore.getState().logout()
    throw new Error('Unauthorized: session expired')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error((body as { error?: string }).error ?? `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function getAgentsBaseUrl(): string {
  return import.meta.env.VITE_AGENTS_URL ?? 'http://localhost:8000'
}
