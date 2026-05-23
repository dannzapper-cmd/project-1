import { mockAgentStatus } from "@/lib/mock-data";
import type { AgentStatus } from "@/lib/types";

interface AgentStatusRowProps {
  /**
   * Optional pre-computed list of agent rows. When omitted, the
   * component falls back to `mockAgentStatus` so existing call
   * sites continue to render identically.
   */
  agents?: AgentStatus[];
}

function getStatusStyles(status: AgentStatus["status"]) {
  switch (status) {
    case "success":
      return {
        border: "border-[--color-success]/30",
        badge: "bg-[--color-success-bg] text-[--color-success]",
        icon: "✓",
        label: "Success",
      };
    case "warning":
      return {
        border: "border-[--color-warning]/30",
        badge: "bg-[--color-warning-bg] text-[--color-warning]",
        icon: "⚠",
        label: "Warning",
      };
    case "failed":
      return {
        border: "border-[--color-error]/30",
        badge: "bg-[--color-error-bg] text-[--color-error]",
        icon: "✗",
        label: "Failed",
      };
    case "running":
      return {
        border: "border-[--accent-secondary]/30",
        badge: "bg-cyan-500/10 text-cyan-400 animate-pulse",
        icon: "●",
        label: "Running",
      };
    case "pending":
    default:
      return {
        border: "border-[--border-subtle]",
        badge: "bg-[--bg-overlay] text-[--text-muted]",
        icon: "○",
        label: "Pending",
      };
  }
}

export function AgentStatusRow({ agents }: AgentStatusRowProps = {}) {
  const rows = agents ?? mockAgentStatus;
  // Use a 5-column layout when only five agents are present (API
  // mode in Phase 6.1/6.2 has no Intake), and the original 6-column
  // layout when the mock six-agent fallback is in use. This keeps
  // tiles a consistent width across both modes.
  const gridColsClass = rows.length === 5 ? "grid-cols-5" : "grid-cols-6";

  return (
    <div className={`grid ${gridColsClass} gap-3`}>
      {rows.map((agent) => {
        const styles = getStatusStyles(agent.status);
        return (
          <div
            key={agent.name}
            className={`bg-[--bg-surface] border ${styles.border} rounded-lg p-4`}
          >
            <p className="text-sm font-medium text-[--text-primary] mb-2">
              {agent.name}
            </p>
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${styles.badge}`}
            >
              <span>{styles.icon}</span>
              {styles.label}
            </span>
            <div className="mt-3 flex items-center gap-2 text-xs text-[--text-muted]">
              <span>{agent.success_rate}</span>
              <span>·</span>
              <span className="font-mono">{agent.avg_latency}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
