"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { TraceEntry } from "@/lib/types";

interface TraceTimelineProps {
  trace: TraceEntry[];
}

function getStatusIcon(status: TraceEntry["status"]) {
  switch (status) {
    case "success":
      return { icon: "✓", color: "text-[--color-success]", bg: "bg-[--color-success]" };
    case "warning":
      return { icon: "⚠", color: "text-[--color-warning]", bg: "bg-[--color-warning]" };
    case "failed":
      return { icon: "✗", color: "text-[--color-error]", bg: "bg-[--color-error]" };
    default:
      return { icon: "○", color: "text-[--text-muted]", bg: "bg-[--text-muted]" };
  }
}

export function TraceTimeline({ trace }: TraceTimelineProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between py-2 hover:bg-[--bg-overlay] rounded-lg px-2 -mx-2 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h4 className="text-xs uppercase tracking-widest text-[--text-muted] font-mono">
            Agent Trace
          </h4>
          <span className="text-xs text-[--text-secondary] bg-[--bg-overlay] px-2 py-0.5 rounded-full">
            {trace.length} steps
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-[--text-muted]" />
        ) : (
          <ChevronDown className="h-4 w-4 text-[--text-muted]" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-4 relative">
          {/* Vertical line */}
          <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-[--border-subtle]" />

          <div className="space-y-4">
            {trace.map((entry, index) => {
              const status = getStatusIcon(entry.status);
              return (
                <div key={index} className="relative pl-8">
                  {/* Dot on the line */}
                  <div
                    className={`absolute left-0 top-1 w-4 h-4 rounded-full ${status.bg} flex items-center justify-center`}
                  >
                    <span className="text-[10px] text-white font-bold">{status.icon}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[--text-primary]">
                        {entry.agent}
                      </span>
                      <span className={`${status.color}`}>{status.icon}</span>
                      <span className="text-xs text-[--text-muted] font-mono bg-[--bg-overlay] px-1.5 py-0.5 rounded">
                        {entry.prompt_version}
                      </span>
                    </div>
                    <p className="text-xs text-[--text-muted] italic">
                      {entry.input_summary}
                    </p>
                    <p className="text-xs text-[--text-secondary]">
                      {entry.output_summary}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-[--text-muted]">
                      <span className="font-mono">{entry.latency}</span>
                      <span>·</span>
                      <span className="font-mono">{entry.tokens} tokens</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
