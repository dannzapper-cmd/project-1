"use client";

import { Upload } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface RunControlsProps {
  /** True after the user has processed a batch in this session. */
  hasLoadedResults?: boolean;
  leadsCount?: number;
}

export function RunControls({
  hasLoadedResults = false,
  leadsCount = 0,
}: RunControlsProps = {}) {
  const scrollToIntake = () => {
    document.getElementById("lead-intake")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

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
            Replay demo is safe and $0. Live batch model runs are disabled
            here; demo access, rate limits, and max-leads protections stay
            enforced.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center rounded-lg border border-[--border-default] p-1 bg-[--bg-overlay]">
            <button
              type="button"
              aria-pressed="true"
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
                      disabled
                      aria-disabled="true"
                      className="btn-disabled !px-3 !py-1.5 !text-xs !font-semibold !shadow-none"
                    >
                      Live model run unavailable
                    </button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-xs">
                    No safe live batch endpoint is exposed in this demo.
                    Replay mode remains cost-controlled, rate limited, and
                    protected by demo access.
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
    </div>
  );
}
