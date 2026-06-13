"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  getLiveDemoStatus,
  postLiveDemoRun,
  postLiveDemoUnlock,
} from "@/lib/api/client";
import {
  clearStoredLiveSessionToken,
  getStoredLiveSessionToken,
  setStoredLiveSessionToken,
} from "@/lib/api/live-demo-access";
import type {
  LiveDemoRunMode,
  LiveDemoRunResponse,
  LiveDemoStatusResponse,
} from "@/lib/api/types";

interface GroqLiveModePanelProps {
  selectedLeadIds?: string[];
  onLiveResult?: (response: LiveDemoRunResponse) => void;
}

function runModeBadgeStyles(mode: LiveDemoRunMode): string {
  switch (mode) {
    case "groq_live":
      return "border-[--color-success]/40 bg-[--color-success]/15 text-[--color-success]";
    case "fallback":
      return "border-[--color-warning]/40 bg-[--color-warning-bg] text-[--color-warning]";
    case "deterministic":
      return "border-[--border-subtle] bg-[--bg-overlay] text-[--text-secondary]";
    case "replay":
    default:
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  }
}

function runModeLabel(mode: LiveDemoRunMode): string {
  switch (mode) {
    case "groq_live":
      return "Groq Live";
    case "fallback":
      return "Fallback";
    case "deterministic":
      return "Deterministic";
    case "replay":
    default:
      return "Replay";
  }
}

export function GroqLiveModePanel({
  selectedLeadIds = [],
  onLiveResult,
}: GroqLiveModePanelProps) {
  const [status, setStatus] = useState<LiveDemoStatusResponse | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [unlockCode, setUnlockCode] = useState("");
  const [unlockMessage, setUnlockMessage] = useState<string | null>(null);
  const [unlocking, setUnlocking] = useState(false);
  const [running, setRunning] = useState(false);
  const [runMessage, setRunMessage] = useState<string | null>(null);
  const [lastResultModes, setLastResultModes] = useState<LiveDemoRunMode[]>([]);

  const refreshStatus = useCallback(async () => {
    try {
      const next = await getLiveDemoStatus();
      setStatus(next);
      setStatusError(null);
    } catch (err) {
      setStatus(null);
      setStatusError(
        err instanceof Error ? err.message : "Could not load live demo status",
      );
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  const handleUnlock = async () => {
    const trimmed = unlockCode.trim();
    if (!trimmed) {
      setUnlockMessage("Enter the Groq Live demo unlock code.");
      return;
    }
    setUnlocking(true);
    setUnlockMessage(null);
    try {
      const response = await postLiveDemoUnlock(trimmed);
      if (response.unlocked && response.session_token) {
        setStoredLiveSessionToken(response.session_token);
        setUnlockCode("");
        setUnlockMessage(response.message);
      } else {
        clearStoredLiveSessionToken();
        setUnlockMessage(response.message);
      }
      await refreshStatus();
    } catch (err) {
      setUnlockMessage(
        err instanceof Error ? err.message : "Unlock request failed.",
      );
    } finally {
      setUnlocking(false);
    }
  };

  const handleClearUnlock = () => {
    clearStoredLiveSessionToken();
    setUnlockMessage("Live demo session cleared. Replay mode remains available.");
    void refreshStatus();
  };

  const handleRunLive = async () => {
    if (selectedLeadIds.length === 0) {
      setRunMessage("Select at least one lead from the results table first.");
      return;
    }
    setRunning(true);
    setRunMessage(null);
    try {
      const response = await postLiveDemoRun({ lead_ids: selectedLeadIds });
      setLastResultModes(response.results.map((item) => item.metadata.run_mode));
      setRunMessage(response.message);
      onLiveResult?.(response);
      await refreshStatus();
    } catch (err) {
      setRunMessage(err instanceof Error ? err.message : "Live run failed.");
    } finally {
      setRunning(false);
    }
  };

  const unlocked = status?.live_mode_unlocked || Boolean(getStoredLiveSessionToken());
  const tooManyLeads =
    status != null && selectedLeadIds.length > status.limits.max_live_leads_per_run;
  const canRun =
    status?.available === true &&
    unlocked &&
    selectedLeadIds.length > 0 &&
    !tooManyLeads &&
    !running;

  const disabledReason = (() => {
    if (statusError) return "Backend unavailable";
    if (!status) return "Loading live mode status…";
    if (!status.groq_api_key_configured) return "GROQ_API_KEY not configured";
    if (!status.live_mode_enabled) return "Live mode disabled on backend";
    if (!unlocked) return "Enter unlock code 555588";
    if (tooManyLeads) {
      return `Too many leads selected (max ${status.limits.max_live_leads_per_run})`;
    }
    if ((status.session_runs_remaining_today ?? 0) <= 0) {
      return "Session daily live run limit reached";
    }
    if ((status.daily_budget_remaining_usd ?? 0) <= 0) {
      return "Daily live demo budget exhausted";
    }
    return null;
  })();

  return (
    <section className="surface-card rounded-lg p-4 space-y-3">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-[--text-primary]">
            Groq Live Demo Mode
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-[--text-secondary]">
            Live mode uses real model calls, is rate-limited, and is intended only
            for small demos. Replay mode remains the default safe path.
          </p>
          <p className="mt-1 text-xs text-[--text-muted]">
            No live web research, no email sending, no CRM writes.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {lastResultModes.map((mode, index) => (
            <span
              key={`${mode}-${index}`}
              className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${runModeBadgeStyles(mode)}`}
            >
              {runModeLabel(mode)}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
        <div className="space-y-2">
          <input
            type="password"
            value={unlockCode}
            onChange={(event) => {
              setUnlockCode(event.target.value);
              setUnlockMessage(null);
            }}
            placeholder="Enter Groq Live unlock code"
            className="h-9 w-full rounded-md border border-[--border-subtle] bg-[--bg-elevated] px-3 text-sm text-[--text-primary] placeholder:text-[--text-muted] focus:outline-none focus:ring-1 focus:ring-[--accent-primary]"
            aria-label="Groq Live demo unlock code"
          />
          {unlockMessage && (
            <p className="text-xs text-[--text-muted]" role="status">
              {unlockMessage}
            </p>
          )}
          {status && (
            <p className="text-xs text-[--text-secondary]">
              Session runs left today: {status.session_runs_remaining_today ?? "—"}
              {" · "}
              Budget left: $
              {(status.daily_budget_remaining_usd ?? 0).toFixed(2)}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void handleUnlock()}
            disabled={unlocking}
            className="btn-secondary !py-2 !text-xs"
          >
            {unlocking ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                Unlocking…
              </>
            ) : (
              "Unlock live mode"
            )}
          </button>
          {unlocked && (
            <button
              type="button"
              onClick={handleClearUnlock}
              className="btn-secondary !py-2 !text-xs"
            >
              Clear unlock
            </button>
          )}
          <button
            type="button"
            onClick={() => void handleRunLive()}
            disabled={!canRun}
            className={canRun ? "btn-primary !py-2 !text-xs" : "btn-disabled !py-2 !text-xs"}
          >
            {running ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                Running…
              </>
            ) : (
              "Run Groq live"
            )}
          </button>
        </div>
      </div>

      {disabledReason && (
        <p className="text-xs text-[--text-muted]" role="status">
          {disabledReason}
        </p>
      )}
      {runMessage && (
        <p className="text-xs text-[--text-secondary]" role="status">
          {runMessage}
        </p>
      )}
      {statusError && (
        <p className="text-xs text-[--color-warning]" role="alert">
          {statusError}
        </p>
      )}
    </section>
  );
}

export { runModeBadgeStyles, runModeLabel };
