import Link from "next/link";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { ExternalLink } from "lucide-react";
import { DemoOnboarding } from "@/components/dashboard/DemoOnboarding";
import { DemoAccessCodePanel } from "@/components/dashboard/DemoAccessCodePanel";
import { ReplayModeBanner } from "@/components/dashboard/ReplayModeBanner";
import { DemoDashboardClient } from "@/components/dashboard/DemoDashboardClient";

export const metadata = {
  title: "Demo Dashboard | LeadForge",
  description: "AI-powered lead processing pipeline demo",
};

export default function DemoPage() {
  const sampleCsvContent = readFileSync(
    join(process.cwd(), "data/demo/leads.csv"),
    "utf-8",
  );

  return (
    <div className="min-h-screen bg-[--bg-base]">
      {/* Replay Mode Banner */}
      <ReplayModeBanner />

      {/* Header */}
      <header className="border-b border-[--border-default] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-[--text-primary]">LeadForge</span>
            <span className="text-xs font-mono text-[--text-muted]">Agentic Core</span>
            <span className="bg-[--accent-primary]/20 text-[--accent-primary] px-2 py-0.5 rounded-full text-xs font-medium ml-2">
              Demo
            </span>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/" className="text-sm text-[--text-secondary] hover:text-[--text-primary] transition-colors">
              Landing
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-[--text-secondary] hover:text-[--text-primary] transition-colors inline-flex items-center gap-1"
            >
              GitHub
              <ExternalLink className="h-3 w-3" />
            </a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <DemoOnboarding />
        <DemoAccessCodePanel />

        {/* Data-driven dashboard sections.
            Reads `DATA_SOURCE` (the only point in the app where it
            is consulted) and renders the metrics row, agent status
            row, and lead table from the normalized view model. */}
        <DemoDashboardClient sampleCsvContent={sampleCsvContent} />
      </main>
    </div>
  );
}
