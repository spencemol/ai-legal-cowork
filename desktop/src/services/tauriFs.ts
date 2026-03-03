/**
 * Thin adapter for Tauri fs/dialog plugins.
 * In Tauri desktop environment: delegates to @tauri-apps/plugin-dialog and @tauri-apps/plugin-fs.
 * In browser / test environment: falls back to browser download mechanism.
 *
 * Tests mock this module directly via vi.mock('../services/tauriFs').
 *
 * The Tauri plugin imports use a runtime string variable so Vite's static analysis
 * does not attempt to resolve the package during non-Tauri (test/browser) builds.
 */

/** Returns true when running inside a Tauri window. */
function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

// Stored as variables to prevent Vite static import analysis from resolving them.
const TAURI_DIALOG_PKG = '@tauri-apps/plugin-dialog'
const TAURI_FS_PKG = '@tauri-apps/plugin-fs'

/**
 * Opens a native save-file dialog and returns the chosen path.
 * Returns null if the user cancels.
 */
export async function showSaveDialog(defaultPath: string): Promise<string | null> {
  if (isTauri()) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mod = await import(/* @vite-ignore */ TAURI_DIALOG_PKG) as any
    return mod.save({ defaultPath }) as Promise<string | null>
  }
  // Browser fallback: just return the suggested filename
  return defaultPath
}

/**
 * Writes text content to a file at the given path.
 * In browser environments triggers a download instead.
 */
export async function writeTextFile(path: string, content: string): Promise<void> {
  if (isTauri()) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mod = await import(/* @vite-ignore */ TAURI_FS_PKG) as any
    const encoder = new TextEncoder()
    await mod.writeFile(path, encoder.encode(content))
    return
  }
  // Browser fallback: trigger anchor download
  const blob = new Blob([content], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = path.split('/').pop() ?? path
  anchor.click()
  URL.revokeObjectURL(url)
}

/**
 * Writes binary (base64-encoded) content to a file at the given path.
 * In browser environments triggers a download instead.
 */
export async function writeBinaryFile(path: string, base64Content: string): Promise<void> {
  if (isTauri()) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mod = await import(/* @vite-ignore */ TAURI_FS_PKG) as any
    const binary = Uint8Array.from(atob(base64Content), (c) => c.charCodeAt(0))
    await mod.writeFile(path, binary)
    return
  }
  // Browser fallback
  const binary = Uint8Array.from(atob(base64Content), (c) => c.charCodeAt(0))
  const blob = new Blob([binary], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = path.split('/').pop() ?? path
  anchor.click()
  URL.revokeObjectURL(url)
}
