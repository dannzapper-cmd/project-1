"use client";

import { Button } from "@/components/ui/button";
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
    <div className="bg-[--bg-surface] border border-[--border-default] rounded-lg p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[--border-subtle] bg-[--bg-elevated]">
            {hasLoadedResults ? (
              <>
                <span className="text-sm text-[--text-primary]">Pipeline results loaded</span>
                <span className="text-[--text-muted]">·</span>
                <span className="text-sm text-[--text-secondary]">
                  {leadsCount} lead{leadsCount === 1 ? "" : "s"} in this run
                </span>
              </>
            ) : (
              <>
                <span className="text-sm text-[--text-primary]">Sample CSV available</span>
                <span className="text-[--text-muted]">·</span>
                <span className="text-sm text-[--text-secondary]">
                  Not loaded yet — use Add Leads below
                </span>
              </>
            )}
          </div>
          <p className="text-xs text-[--text-muted] mt-2">
            Replay demo is free. Live Groq is backend API-only and opt-in.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center rounded-lg border border-[--border-default] p-1">
            <button
              type="button"
              aria-pressed="true"
              className="px-3 py-1.5 rounded-md text-sm font-medium bg-[--accent-primary] text-white"
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
                      className="px-3 py-1.5 rounded-md text-sm font-medium text-[--text-muted] opacity-50 cursor-not-allowed"
                    >
                      Live API (requires backend)
                    </button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>
                    Live Groq is backend-only and opt-in. This demo view stays
                    on replay unless backend API mode is configured separately.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    size="lg"
                    disabled
                    aria-disabled="true"
                    className="bg-[--accent-primary] hover:bg-[--accent-primary]/90 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {hasLoadedResults ? "Process Leads (results loaded)" : "Process Leads"}
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  {hasLoadedResults
                    ? "Results for this run are shown below. Use Add Leads to process another batch."
                    : "No leads loaded yet. Paste or upload sample data in Add Leads, then process to run the pipeline."}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Button
            variant="outline"
            onClick={scrollToIntake}
            className="border-[--border-default] text-[--text-secondary]"
          >
            <Upload className="h-4 w-4 mr-2" />
            Add Leads
          </Button>
        </div>
      </div>
    </div>
  );
}
