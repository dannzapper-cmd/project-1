"use client";

import { Button } from "@/components/ui/button";
import { Check, Download } from "lucide-react";
import type { Lead } from "@/lib/types";

interface HumanReviewControlsProps {
  status: Lead["status"];
  onStatusChange: (status: Lead["status"]) => void;
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

export function HumanReviewControls({ status, onStatusChange }: HumanReviewControlsProps) {
  const hasBeenReviewed = status !== "Pending Review";

  return (
    <div className="bg-[--bg-elevated] border-t border-[--border-default] px-6 py-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs text-[--text-muted]">Status:</span>
        {getStatusBadge(status)}
      </div>

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

        <Button
          variant="outline"
          className="px-4 py-2 text-sm border-[--border-default] text-[--text-secondary] hover:bg-[--bg-overlay]"
        >
          Regenerate Email
        </Button>

        {hasBeenReviewed && (
          <Button
            variant="outline"
            className="px-4 py-2 text-sm border-[--accent-primary] text-[--accent-primary] hover:bg-[--accent-primary]/10 ml-auto"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Lead
          </Button>
        )}
      </div>

      <p className="text-xs text-[--text-muted] mt-3">
        Approving this lead does not send any email. It marks the lead as reviewed and ready for export.
      </p>
    </div>
  );
}
