export const DEMO_ACCESS_HEADER = "X-LeadForge-Demo-Key";
export const DEMO_ACCESS_STORAGE_KEY = "leadforge-demo-access-code";

let inMemoryDemoAccessCode: string | null = null;

export function getStoredDemoAccessCode(): string | null {
  if (typeof window === "undefined") return inMemoryDemoAccessCode;
  try {
    const value = window.sessionStorage.getItem(DEMO_ACCESS_STORAGE_KEY);
    const trimmed = value?.trim();
    if (trimmed) {
      inMemoryDemoAccessCode = trimmed;
      return trimmed;
    }
  } catch {
    // sessionStorage may be unavailable in some privacy modes.
  }
  return inMemoryDemoAccessCode;
}

export function setStoredDemoAccessCode(code: string): void {
  const trimmed = code.trim();
  inMemoryDemoAccessCode = trimmed || null;
  if (typeof window === "undefined") return;
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
  inMemoryDemoAccessCode = null;
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

