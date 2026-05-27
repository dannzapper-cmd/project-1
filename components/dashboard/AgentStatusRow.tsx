import { mockAgentStatus } from "@/lib/mock-data";
import type { AgentStatus } from "@/lib/types";

interface AgentStatusRowProps {
  /**
   * Optional pre-computed list of agent rows. When omitted, the
   * component falls back to `mockAgentStatus` so existing call
   * sites continue to render identically.
   */
  agents?: AgentStatus[];
  replayMode?: boolean;
}

function getDisplayStatus(
  status: AgentStatus["status"],
  replayMode: boolean,
): AgentStatus["status"] {
  return replayMode && status === "running" ? "pending" : status;
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
        badge: "bg-[--accent-secondary]/10 text-[--accent-secondary] animate-pulse",
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

export function AgentStatusRow({
  agents,
  replayMode = true,
}: AgentStatusRowProps = {}) {
  const rows = agents ?? mockAgentStatus;

  return (
    <section
      aria-labelledby="agent-activity-heading"
      className="surface-card rounded-lg p-5 space-y-4"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[10px] font-mono uppercase tracking-widest text-[--accent-primary] mb-1">
            Agent workflow
          </p>
          <h2
            id="agent-activity-heading"
            className="text-sm font-semibold text-[--text-primary]"
          >
            Six-agent pipeline
          </h2>
          <p className="text-xs text-[--text-muted] mt-0.5">
            Intake → Research → Qualifier → Strategist → Email Drafter → QA
            Evaluator. Each card shows role, status, and output summary for this
            run.
          </p>
        </div>
        {replayMode && (
          <span className="self-start rounded-full border border-[--color-warning]/30 bg-[--color-warning-bg] px-3 py-1 text-xs font-medium text-[--color-warning]">
            Replay/demo mode - statuses reflect saved outputs, not live agents running now.
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {rows.map((agent) => {
          const displayStatus = getDisplayStatus(agent.status, replayMode);
          const styles = getStatusStyles(displayStatus);
          return (
            <div
              key={agent.name}
              className={`bg-[--bg-elevated] border ${styles.border} rounded-lg p-4 min-h-44 shadow-sm`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-[--text-primary]">
                  {agent.name}
                </p>
                <span
                  className={`inline-flex shrink-0 items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${styles.badge}`}
                >
                  <span>{styles.icon}</span>
                  {styles.label}
                </span>
              </div>
              {agent.description && (
                <p className="mt-3 text-xs text-[--text-secondary] leading-relaxed">
                  {agent.description}
                </p>
              )}
              {agent.output_summary && (
                <div className="mt-3">
                  <p className="text-[10px] uppercase tracking-wide text-[--text-muted] mb-1">
                    Output summary
                  </p>
                  <p className="text-xs text-[--text-secondary] leading-relaxed">
                    {agent.output_summary}
                  </p>
                </div>
              )}
              <div className="mt-3 flex items-center gap-2 text-xs text-[--text-muted]">
                <span>{agent.success_rate}</span>
                <span>·</span>
                <span className="font-mono">{agent.avg_latency}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
