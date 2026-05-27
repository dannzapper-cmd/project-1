"use client";

/**
 * Block 10E — Live Web Research MVP UI.
 *
 * A single, manual-trigger panel that calls
 * `POST /api/research/live-company` for the currently selected
 * lead. Behavior:
 *
 * - Never fires on mount. The user must click "Run live research".
 * - Renders disabled / unavailable / rate-limited / timeout /
 *   no-evidence / error states from the structured response — the
 *   endpoint always returns HTTP 200 so the frontend has one
 *   predictable shape to consume.
 * - Cited evidence cards include URL, source domain, snippet,
 *   confidence, and a short rationale that is built backend-side
 *   from lead context only (never from an LLM).
 * - The panel is intentionally framed as "Manual live research /
 *   Uses public web results when enabled" so users do not confuse
 *   it with the deterministic / replay context.
 */

import { ExternalLink, Search, Loader2 } from "lucide-react";
import { useState } from "react";

import { ApiError, postLiveCompanyResearch } from "@/lib/api/client";
import type { LeadDetail } from "@/lib/types";
import type {
  LiveResearchEvidenceCard,
  LiveResearchResponse,
} from "@/lib/api/types";

interface LiveResearchPanelProps {
  lead: LeadDetail | null;
  /**
   * Optional injection point for tests. Production callers leave
   * undefined and the component uses the default API client.
   */
  postLiveResearch?: typeof postLiveCompanyResearch;
}

function confidenceClasses(
  confidence: LiveResearchEvidenceCard["confidence"],
): string {
  switch (confidence) {
    case "High":
      return "text-[--color-success]";
    case "Medium":
      return "text-[--color-warning]";
    case "Low":
      return "text-[--text-muted]";
    default:
      return "text-[--text-muted]";
  }
}

function buildRequest(lead: LeadDetail) {
  return {
    company_name: lead.company,
    website: lead.website || null,
    industry: lead.industry || null,
    country: lead.country || null,
    notes: null,
  };
}

interface DisabledNoticeProps {
  status: LiveResearchResponse["status"];
  message: string;
}

function ResultBanner({ status, message }: DisabledNoticeProps) {
  // One banner component covers every non-"ok" terminal state. The
  // visual language is intentionally soft (warning surface) so
  // users see this as informational, never as an error toast.
  const tone =
    status === "ok"
      ? "border-[--color-success]/30 bg-[--color-success-bg]/20 text-[--color-success]"
      : status === "rate_limited" || status === "timeout"
        ? "border-[--color-warning]/30 bg-[--color-warning-bg]/30 text-[--color-warning]"
        : "border-[--border-default] bg-[--bg-overlay] text-[--text-secondary]";
  return (
    <div
      className={`mt-3 rounded-lg border px-3 py-2 text-xs ${tone}`}
      role="status"
    >
      {message}
    </div>
  );
}

function RunDetails({ response }: { response: LiveResearchResponse }) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] text-[--text-muted]">
      <span>
        Provider: <span className="font-mono">{response.provider}</span>
      </span>
      <span>
        Mode: <span className="font-mono">{response.run_mode}</span>
      </span>
      {response.confidence && (
        <span>
          Overall confidence:{" "}
          <span className="font-mono">{response.confidence}</span>
        </span>
      )}
      <span>
        Daily requests:{" "}
        <span className="font-mono">{response.estimated_request_count}</span>
      </span>
    </div>
  );
}

export function LiveResearchPanel({
  lead,
  postLiveResearch = postLiveCompanyResearch,
}: LiveResearchPanelProps) {
  const [response, setResponse] = useState<LiveResearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!lead) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await postLiveResearch(buildRequest(lead));
      setResponse(result);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `Live research request failed (HTTP ${err.status}). The backend may be unavailable or warming up — try again in a moment.`
          : err instanceof Error
            ? err.message
            : "Unexpected error running live research.";
      setError(message);
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const buttonDisabled = isLoading || !lead;

  return (
    <section
      className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-4"
      aria-labelledby="live-research-heading"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3
            id="live-research-heading"
            className="text-sm font-semibold text-[--text-primary]"
          >
            Manual live research
          </h3>
          <p className="text-xs text-[--text-muted] mt-1">
            Uses public web results when enabled. One company at a time.
          </p>
        </div>
        <span className="rounded-full border border-[--border-subtle] bg-[--bg-overlay] px-2 py-0.5 text-[10px] font-medium text-[--text-muted]">
          Off by default
        </span>
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={buttonDisabled}
        className="btn-secondary mt-4 !text-xs disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Researching…
          </>
        ) : (
          <>
            <Search className="h-3 w-3" />
            Run live research
          </>
        )}
      </button>

      <p className="mt-2 text-[10px] text-[--text-muted]">
        Cited public-web sources only. Not a guaranteed recommendation —
        always verify before relying on results.
      </p>

      {error && (
        <div
          className="mt-3 rounded-lg border border-[--color-error]/30 bg-[--color-error-bg]/30 px-3 py-2 text-xs text-[--color-error]"
          role="alert"
        >
          {error}
        </div>
      )}

      {response && (
        <>
          {response.status === "ok" ? (
            <>
              <ResultBanner
                status={response.status}
                message={response.user_message}
              />
              <div className="mt-3 grid grid-cols-1 gap-2">
                {response.evidence_cards.map((card) => (
                  <div
                    key={card.url}
                    className="bg-[--bg-elevated] border border-[--border-subtle] rounded-lg p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-[--text-primary]">
                        {card.title}
                      </p>
                      <span className="shrink-0 text-[10px] text-[--text-muted] bg-[--bg-overlay] px-2 py-0.5 rounded-full">
                        {card.source_type}
                      </span>
                    </div>
                    <a
                      href={card.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-flex items-center gap-1 text-xs text-[--accent-primary] hover:underline"
                    >
                      {card.source_domain}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                    {card.snippet && (
                      <p className="text-xs text-[--text-secondary] mt-2 leading-relaxed">
                        {card.snippet}
                      </p>
                    )}
                    <div className="flex items-center gap-1 mt-2">
                      <span className={confidenceClasses(card.confidence)}>
                        ●
                      </span>
                      <span className="text-[10px] text-[--text-muted]">
                        {card.confidence} confidence
                      </span>
                    </div>
                    <p className="text-[10px] text-[--text-muted] mt-2 italic">
                      {card.why_it_matters}
                    </p>
                  </div>
                ))}
              </div>
              {response.information_risks.length > 0 && (
                <div className="mt-3 rounded-lg border border-[--color-warning]/30 bg-[--color-warning-bg]/20 px-3 py-2">
                  <p className="text-[10px] uppercase tracking-widest text-[--color-warning] font-mono mb-1">
                    Information risks
                  </p>
                  <ul className="space-y-1">
                    {response.information_risks.map((risk) => (
                      <li
                        key={risk}
                        className="text-xs text-[--text-secondary]"
                      >
                        - {risk}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <RunDetails response={response} />
            </>
          ) : (
            <>
              <ResultBanner
                status={response.status}
                message={response.user_message}
              />
              {response.warnings.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {response.warnings.map((warning) => (
                    <li
                      key={warning}
                      className="text-[10px] text-[--text-muted]"
                    >
                      · {warning}
                    </li>
                  ))}
                </ul>
              )}
              <RunDetails response={response} />
            </>
          )}
        </>
      )}
    </section>
  );
}

export default LiveResearchPanel;
