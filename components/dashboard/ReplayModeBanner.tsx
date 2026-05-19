"use client";

import { useState } from "react";
import { X } from "lucide-react";

export function ReplayModeBanner() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full text-xs font-medium">
            Demo Mode
          </span>
          <span className="text-xs text-amber-300">
            Showing pre-computed results from a saved run. No model calls are made. No cost is incurred.
          </span>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="text-amber-300/60 hover:text-amber-300 transition-colors"
          aria-label="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
