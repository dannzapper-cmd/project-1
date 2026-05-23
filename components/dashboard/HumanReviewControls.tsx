"use client";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Check, Download } from "lucide-react";
import type { Lead } from "@/lib/types";

interface HumanReviewControlsProps {
  status: Lead["status"];
  onStatusChange: (status: Lead["status"]) => void;
  /**
   * Triggers a local CSV download of the currently reviewed lead.
   * When omitted, the Export CSV button stays disabled with the
   * "coming soon" copy from Phase 7.2 so this component remains
   * usable in tests or other call sites that do not wire export.
   * The Block 7.4 LeadDetailDrawer always provides this handler.
   */
  onExportLead?: () => void;
}

function getStatusBadge(status: Lead["status"]) {
  switch (status) {
    case "Approved":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-[--color-success-bg] text-[--color-success]">
          <Check className="h-3 w-3" />
          Approved
        </span>
      );
    case "Rejected":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-[--color-error-bg] text-[--color-error]">
          Rejected
        </span>
      );
    case "Needs Edit":
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-[--color-warning-bg] text-[--color-warning]">
          Needs Edit
        </span>
      );
    case "Pending Review":
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-[--accent-primary]/10 text-[--accent-primary]">
          Pending Review
        </span>
      );
  }
}

export function HumanReviewControls({
  status,
  onStatusChange,
  onExportLead,
}: HumanReviewControlsProps) {
  const hasBeenReviewed = status !== "Pending Review";
  const canExport = hasBeenReviewed && onExportLead !== undefined;

  return (
    <div className="bg-[--bg-elevated] border-t border-[--border-default] px-6 py-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs text-[--text-muted]">Status:</span>
        {getStatusBadge(status)}
      </div>

      <TooltipProvider>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => onStatusChange("Approved")}
            disabled={status === "Approved"}
            className={`px-4 py-2 text-sm font-medium ${
              status === "Approved"
                ? "bg-[--color-success]/50 text-white cursor-not-allowed"
                : "bg-[--color-success] hover:brightness-110 text-white"
            }`}
          >
            {status === "Approved" ? (
              <>
                <Check className="h-4 w-4 mr-1" />
                Approved
              </>
            ) : (
              "Approve"
            )}
          </Button>

          <Button
            onClick={() => onStatusChange("Rejected")}
            disabled={status === "Rejected"}
            variant="outline"
            className={`px-4 py-2 text-sm border-[--color-error] text-[--color-error] hover:bg-[--color-error-bg] ${
              status === "Rejected" ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            Reject
          </Button>

          <Button
            onClick={() => onStatusChange("Needs Edit")}
            disabled={status === "Needs Edit"}
            variant="outline"
            className={`px-4 py-2 text-sm border-[--color-warning] text-[--color-warning] hover:bg-[--color-warning-bg] ${
              status === "Needs Edit" ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            Needs Edit
          </Button>

          {/*
            Regenerate Email and Export Lead are intentionally inert
            in this demo. The dashboard has no backend write surface
            for email regeneration (no model is invoked from the UI)
            and no export pipeline. We disable both buttons rather
            than hide them so reviewers can still see the planned
            human-in-the-loop affordances; tooltips state the demo
            limitation explicitly.
          */}
          <Tooltip>
            <TooltipTrigger asChild>
              <span>
                <Button
                  disabled
                  aria-disabled="true"
                  variant="outline"
                  className="px-4 py-2 text-sm border-[--border-default] text-[--text-secondary] opacity-50 cursor-not-allowed"
                >
                  Regenerate email (coming soon)
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              <p>Regenerate — not available in demo mode. No model is called from the dashboard.</p>
            </TooltipContent>
          </Tooltip>

          {/*
            Block 7.4: Export becomes a real local CSV download once
            the lead has been reviewed (status !== "Pending Review"
            and onExportLead is wired). For pending leads the button
            stays disabled with a tooltip that explains the gate.
            No backend call, no persistence — the file is built in
            memory and handed to the browser as a Blob.
          */}
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="ml-auto">
                <Button
                  type="button"
                  onClick={canExport ? onExportLead : undefined}
                  disabled={!canExport}
                  aria-disabled={!canExport}
                  variant="outline"
                  className={
                    canExport
                      ? "px-4 py-2 text-sm border-[--accent-primary] text-[--accent-primary] hover:bg-[--accent-primary]/10"
                      : "px-4 py-2 text-sm border-[--border-default] text-[--text-secondary] opacity-50 cursor-not-allowed"
                  }
                >
                  <Download className="h-4 w-4 mr-2" />
                  {canExport
                    ? "Export CSV"
                    : onExportLead === undefined
                    ? "Export CSV (coming soon)"
                    : "Export CSV"}
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              {onExportLead === undefined ? (
                <p>Export CSV — not available in demo mode.</p>
              ) : !hasBeenReviewed ? (
                <p>Review this lead before exporting.</p>
              ) : (
                <p>Download this reviewed lead as CSV.</p>
              )}
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>

      <p className="text-xs text-[--text-muted] mt-3">
        Approving a lead only marks it locally for review in this demo. No email is sent,
        no data is written to the backend, and the status is not persisted across page reloads.
        Exporting downloads a CSV to your computer — it does not push the lead anywhere.
      </p>
    </div>
  );
}
