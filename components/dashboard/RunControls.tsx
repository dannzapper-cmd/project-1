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
              className="px-3 py-1.5 rounded-md text-sm font-medium bg-[--accent-primary] text-white"
            >
              Replay Mode
            </button>
            <span
              className="px-3 py-1.5 rounded-md text-sm font-medium text-[--text-muted]"
            >
              Live API-only
            </span>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    size="lg"
                    disabled
                    className="bg-[--accent-primary] hover:bg-[--accent-primary]/90 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Process Leads
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>Pipeline execution is loaded from mock/API data; live Groq is invoked only through the backend POST endpoint.</p>
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
