/**
 * Secure storage abstraction.
 * On Android: uses Capacitor Preferences (sandboxed, encrypted on Android 6+).
 * On web: falls back to sessionStorage (cleared on tab close — more secure than localStorage).
 */

const isCapacitor = () =>
  typeof window !== 'undefined' && window?.Capacitor?.isNativePlatform?.()

let _Preferences = null
async function getPreferences() {
  if (!_Preferences) {
    try {
      const mod = await import('@capacitor/preferences')
      _Preferences = mod.Preferences
    } catch {
      _Preferences = null
    }
  }
  return _Preferences
}

export async function secureSet(key, value) {
  if (isCapacitor()) {
    const P = await getPreferences()
    if (P) { await P.set({ key, value }); return }
  }
  // Web fallback — sessionStorage (not persisted across tabs)
  sessionStorage.setItem(key, value)
}

export async function secureGet(key) {
  if (isCapacitor()) {
    const P = await getPreferences()
    if (P) {
      const { value } = await P.get({ key })
      return value
    }
  }
  return sessionStorage.getItem(key)
}

export async function secureRemove(key) {
  if (isCapacitor()) {
    const P = await getPreferences()
    if (P) { await P.remove({ key }); return }
  }
  sessionStorage.removeItem(key)
}

// ── Backend URL config ────────────────────────────────────────────────────────
const DEFAULT_URL = import.meta.env.VITE_API_URL || 'http://10.0.2.2:8000'

export async function getBackendUrl() {
  const stored = await secureGet('backend_url')
  return (stored || DEFAULT_URL).replace(/\/$/, '')
}

export async function setBackendUrl(url) {
  await secureSet('backend_url', url.replace(/\/$/, ''))
}
