export const DEMO_ACCESS_HEADER = "X-LeadForge-Demo-Key";
export const DEMO_ACCESS_STORAGE_KEY = "leadforge-demo-access-code";

export function getStoredDemoAccessCode(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.sessionStorage.getItem(DEMO_ACCESS_STORAGE_KEY);
    return value && value.trim() ? value.trim() : null;
  } catch {
    return null;
  }
}

export function setStoredDemoAccessCode(code: string): void {
  if (typeof window === "undefined") return;
  const trimmed = code.trim();
  try {
    if (trimmed) {
      window.sessionStorage.setItem(DEMO_ACCESS_STORAGE_KEY, trimmed);
    } else {
      window.sessionStorage.removeItem(DEMO_ACCESS_STORAGE_KEY);
    }
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
}

export function clearStoredDemoAccessCode(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(DEMO_ACCESS_STORAGE_KEY);
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
}

export function getDemoAccessHeaders(): Record<string, string> {
  const code = getStoredDemoAccessCode();
  return code ? { [DEMO_ACCESS_HEADER]: code } : {};
}

