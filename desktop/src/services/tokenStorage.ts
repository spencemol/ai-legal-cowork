// Abstract token storage — uses localStorage in browser/test, Tauri secure store in production
const TOKEN_KEY = 'auth_token'
const STORE_PATH = '.settings.dat'

function isTauriEnv(): boolean {
  return typeof window !== 'undefined' && '__TAURI__' in window
}

async function getTauriStore() {
  const { Store } = await import('@tauri-apps/plugin-store')
  return Store.load(STORE_PATH)
}

export async function saveToken(token: string): Promise<void> {
  if (isTauriEnv()) {
    const store = await getTauriStore()
    await store.set(TOKEN_KEY, token)
  } else {
    localStorage.setItem(TOKEN_KEY, token)
  }
}

export async function getToken(): Promise<string | null> {
  if (isTauriEnv()) {
    const store = await getTauriStore()
    const value = await store.get<string>(TOKEN_KEY)
    return value ?? null
  } else {
    return localStorage.getItem(TOKEN_KEY)
  }
}

export async function clearToken(): Promise<void> {
  if (isTauriEnv()) {
    const store = await getTauriStore()
    await store.set(TOKEN_KEY, null)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}
