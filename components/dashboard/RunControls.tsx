"use client";

import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function RunControls() {
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
            <span className="text-sm text-[--text-primary]">Sample Dataset</span>
            <span className="text-[--text-muted]">·</span>
            <span className="text-sm text-[--text-secondary]">10 B2B leads</span>
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
                    Live Groq runs through the backend only. Configure the API in
                    Block 11; this demo view stays on replay.
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
                    Process Leads (sample loaded)
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  Sample results are already loaded in replay mode. Use Add Leads
                  when the backend is available, or review the table below.
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
