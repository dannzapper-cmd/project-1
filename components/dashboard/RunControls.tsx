"use client";

import { Upload } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { LiveDemoStatusResponse } from "@/lib/api/types";
import type { SystemStatusResponse } from "@/lib/api/types";

interface RunControlsProps {
  /** True after the user has processed a batch in this session. */
  hasLoadedResults?: boolean;
  leadsCount?: number;
  systemStatus?: SystemStatusResponse | null;
  systemStatusError?: string | null;
  liveDemoStatus?: LiveDemoStatusResponse | null;
  pipelineMode?: "replay" | "groq_live";
}

export function RunControls({
  hasLoadedResults = false,
  leadsCount = 0,
  systemStatus = null,
  systemStatusError = null,
  liveDemoStatus = null,
  pipelineMode = "replay",
}: RunControlsProps = {}) {
  const scrollToIntake = () => {
    document.getElementById("lead-intake")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };
  const scrollToResults = () => {
    const target =
      document.getElementById("lead-results") ??
      document.getElementById("lead-intake");
    target?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const controlledLiveAvailable =
    liveDemoStatus?.available === true ||
    (systemStatus?.live_email_regenerate_configured === true &&
      systemStatus.live_single_lead_only === true &&
      systemStatus.public_live_batch_enabled === false);
  const liveButtonLabel =
    pipelineMode === "groq_live"
      ? "Groq Live Mode"
      : controlledLiveAvailable
        ? "Groq Live Mode — unlock below"
        : "Groq Live Mode — backend required";
  const liveHelper =
    pipelineMode === "groq_live"
      ? "Groq Live Demo Mode is active for controlled runs. Replay remains available for safe demos."
      : controlledLiveAvailable
        ? "Replay mode is active. Unlock Groq Live Demo Mode below for rate-limited real model calls."
        : "Replay mode is active. Groq Live runs require backend configuration, unlock code, and rate limits.";
  const liveTooltip =
    pipelineMode === "groq_live"
      ? "Controlled Groq live runs are enabled for this session."
      : controlledLiveAvailable
        ? "Enter the reviewer unlock code in the Groq Live panel to enable controlled live runs."
        : "Replay mode is active. Groq Live requires backend configuration.";

  return (
    <div className="surface-card rounded-lg p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <span className="inline-flex items-center gap-2 rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2.5 py-1 text-xs text-[--text-secondary]">
            {hasLoadedResults ? (
              <>
                <span className="font-medium text-[--text-primary]">Results loaded</span>
                <span className="text-[--text-muted]">·</span>
                <span>
                  {leadsCount} lead{leadsCount === 1 ? "" : "s"} in this run
                </span>
              </>
            ) : (
              <>
                <span className="font-medium text-[--text-primary]">Sample CSV available</span>
                <span className="text-[--text-muted]">·</span>
                <span>Not loaded yet</span>
              </>
            )}
          </span>
          <p className="text-xs text-[--text-muted] mt-2">
            Replay demo is safe and $0. Live Groq is controlled, backend-only,
            and single-lead where enabled; public live batch model runs are not
            exposed.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center rounded-lg border border-[--border-default] p-1 bg-[--bg-overlay]">
            <button
              type="button"
              aria-pressed={pipelineMode === "replay"}
              className="px-3 py-1.5 rounded-md text-xs font-semibold bg-[--accent-primary] text-white"
            >
              Replay Mode
            </button>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <button
                      type="button"
                      disabled={pipelineMode !== "groq_live"}
                      aria-pressed={pipelineMode === "groq_live"}
                      aria-disabled={pipelineMode !== "groq_live"}
                      title={liveTooltip}
                      className={
                        pipelineMode === "groq_live"
                          ? "px-3 py-1.5 rounded-md text-xs font-semibold bg-[--accent-primary] text-white"
                          : "btn-disabled !px-3 !py-1.5 !text-xs !font-semibold !shadow-none"
                      }
                    >
                      {liveButtonLabel}
                    </button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-xs">
                    {liveTooltip}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <button
            type="button"
            onClick={scrollToIntake}
            className="btn-primary btn-hero"
          >
            <Upload className="h-4 w-4" aria-hidden />
            Add Leads
          </button>
        </div>
      </div>
      {!hasLoadedResults && (
        <p className="text-xs text-[--text-secondary] mt-3 border-t border-[--border-subtle] pt-3">
          Use <strong className="font-medium text-[--text-primary]">Add Leads</strong> to
          paste or upload data, then <strong className="font-medium text-[--text-primary]">Preview Leads</strong> and{" "}
          <strong className="font-medium text-[--text-primary]">Process</strong> in that section.
        </p>
      )}
      <p className="text-xs text-[--text-secondary] mt-3 border-t border-[--border-subtle] pt-3">
        {liveHelper}
        {systemStatusError ? (
          <span className="block mt-1 text-[--text-muted]">
            Backend status could not be confirmed, so live controls stay disabled.
          </span>
        ) : null}
      </p>
    </div>
  );
}
