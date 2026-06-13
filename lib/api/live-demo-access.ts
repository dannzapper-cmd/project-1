export const LIVE_SESSION_HEADER = "X-LeadForge-Live-Session";
export const LIVE_SESSION_STORAGE_KEY = "leadforge-live-demo-session";

let inMemoryLiveSessionToken: string | null = null;

export function getStoredLiveSessionToken(): string | null {
  if (typeof window === "undefined") return inMemoryLiveSessionToken;
  try {
    const value = window.sessionStorage.getItem(LIVE_SESSION_STORAGE_KEY);
    const trimmed = value?.trim();
    if (trimmed) {
      inMemoryLiveSessionToken = trimmed;
      return trimmed;
    }
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
  return inMemoryLiveSessionToken;
}

export function setStoredLiveSessionToken(token: string): void {
  const trimmed = token.trim();
  inMemoryLiveSessionToken = trimmed || null;
  if (typeof window === "undefined") return;
  try {
    if (trimmed) {
      window.sessionStorage.setItem(LIVE_SESSION_STORAGE_KEY, trimmed);
    } else {
      window.sessionStorage.removeItem(LIVE_SESSION_STORAGE_KEY);
    }
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
}

export function clearStoredLiveSessionToken(): void {
  inMemoryLiveSessionToken = null;
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(LIVE_SESSION_STORAGE_KEY);
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
}

export function getLiveSessionHeaders(): Record<string, string> {
  const token = getStoredLiveSessionToken();
  return token ? { [LIVE_SESSION_HEADER]: token } : {};
}
