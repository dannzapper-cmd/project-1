"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function RunControls() {
  const [mode, setMode] = useState<"replay" | "live">("replay");

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
            Estimated cost: ~$0.30–$0.50 for live run
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center rounded-lg border border-[--border-default] p-1">
            <button
              onClick={() => setMode("replay")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === "replay"
                  ? "bg-[--accent-primary] text-white"
                  : "text-[--text-secondary] hover:text-[--text-primary]"
              }`}
            >
              Replay Mode
            </button>
            <button
              onClick={() => setMode("live")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                mode === "live"
                  ? "bg-[--accent-primary] text-white"
                  : "text-[--text-secondary] hover:text-[--text-primary]"
              }`}
            >
              Live Mode
            </button>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    size="lg"
                    disabled={mode === "replay"}
                    className="bg-[--accent-primary] hover:bg-[--accent-primary]/90 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Process Leads
                  </Button>
                </span>
              </TooltipTrigger>
              {mode === "replay" && (
                <TooltipContent>
                  <p>Switch to Live mode to run the pipeline</p>
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>

          <Button variant="outline" className="border-[--border-default] text-[--text-secondary] hover:bg-[--bg-overlay]">
            <Upload className="h-4 w-4 mr-2" />
            Upload CSV
          </Button>
        </div>
      </div>
    </div>
  );
}
