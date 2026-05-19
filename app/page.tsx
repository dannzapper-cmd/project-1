import { HeroSection } from "@/components/landing/HeroSection"
import { ProblemSection } from "@/components/landing/ProblemSection"
import { SolutionSection } from "@/components/landing/SolutionSection"
import { AgentWorkflowPreview } from "@/components/landing/AgentWorkflowPreview"
import { ArchitectureSection } from "@/components/landing/ArchitectureSection"
import { FinalCTASection } from "@/components/landing/FinalCTASection"

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[--bg-base]">
      <HeroSection />
      <ProblemSection />
      <SolutionSection />
      <AgentWorkflowPreview />
      <ArchitectureSection />
      <FinalCTASection />
    </main>
  )
}
