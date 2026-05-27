"use client";

import { useEffect, useState } from "react";

import {
  clearStoredDemoAccessCode,
  getStoredDemoAccessCode,
  setStoredDemoAccessCode,
} from "@/lib/api/demo-access";

export function DemoAccessCodePanel() {
  const [code, setCode] = useState("");
  const [hasStoredCode, setHasStoredCode] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredDemoAccessCode();
    setHasStoredCode(Boolean(stored));
  }, []);

  const handleSave = () => {
    const trimmed = code.trim();
    if (!trimmed) {
      setMessage("Enter the private demo access code before saving.");
      return;
    }
    setStoredDemoAccessCode(trimmed);
    setCode("");
    setHasStoredCode(true);
    setMessage("Demo access code saved for this browser tab.");
  };

  const handleClear = () => {
    clearStoredDemoAccessCode();
    setHasStoredCode(false);
    setMessage("Demo access code cleared.");
  };

  return (
    <section className="surface-card rounded-lg p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-[--text-primary]">
            Private demo access
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-[--text-secondary]">
            If the backend has a demo access code configured, Add Leads, Process,
            Live Research, and the live assistant require the code shared with the
            demo link. It is stored only in this tab&apos;s sessionStorage.
          </p>
          {hasStoredCode && (
            <p className="mt-1 text-xs text-[--color-success]">
              Access code is saved for this browser tab.
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            type="password"
            value={code}
            onChange={(event) => {
              setCode(event.target.value);
              setMessage(null);
            }}
            placeholder="Enter demo access code"
            className="h-9 rounded-md border border-[--border-subtle] bg-[--bg-elevated] px-3 text-sm text-[--text-primary] placeholder:text-[--text-muted] focus:outline-none focus:ring-1 focus:ring-[--accent-primary]"
            aria-label="Private demo access code"
          />
          <button type="button" onClick={handleSave} className="btn-primary !py-2 !text-xs">
            Save code
          </button>
          {hasStoredCode && (
            <button
              type="button"
              onClick={handleClear}
              className="btn-secondary !py-2 !text-xs"
            >
              Clear
            </button>
          )}
        </div>
      </div>
      {message && (
        <p className="mt-2 text-xs text-[--text-muted]" role="status">
          {message}
        </p>
      )}
    </section>
  );
}

