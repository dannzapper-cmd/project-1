"use client"

import { motion } from "framer-motion"
import { CheckCircle } from "lucide-react"

const agents = [
  {
    number: "01",
    name: "Intake Agent",
    description:
      "Validates and normalizes raw lead data. Catches missing fields, unknown industries, invalid websites.",
    output: "Clean lead object with validation flags",
  },
  {
    number: "02",
    name: "Research Agent",
    description:
      "Builds company context from the knowledge base and lead signals. Creates evidence cards — never invents sources.",
    output: "Evidence cards, opportunity signals, company summary",
  },
  {
    number: "03",
    name: "Qualify Agent",
    description:
      "Assigns a fit score (0-100) and priority tier based on ICP rules. Returns reasons for every score.",
    output: "Fit score, priority tier, qualification reasons",
  },
  {
    number: "04",
    name: "Strategize Agent",
    description:
      "Selects the best sales angle given research and qualification. Produces a pain hypothesis.",
    output: "Pain hypothesis, sales angle, core message",
  },
  {
    number: "05",
    name: "Draft Agent",
    description:
      "Generates a personalized outreach email grounded in evidence and strategy.",
    output: "Subject line, email body, personalization notes",
  },
  {
    number: "06",
    name: "Evaluate Agent",
    description:
      "Scores output quality across 5 dimensions. Flags hallucination risk before human review.",
    output: "QA scores, hallucination risk, approval recommendation",
  },
]

const metrics = [
  "~45 seconds per lead in live mode",
  "~$0.02-$0.05 per lead",
  "Replay mode: $0 — zero model calls",
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

export function AgentWorkflowPreview() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Label */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-xs font-mono uppercase tracking-widest text-[--accent-primary] mb-4"
        >
          How It Works
        </motion.p>

        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] max-w-2xl mb-4"
        >
          Six agents. One pipeline. Full traceability.
        </motion.h2>

        {/* Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="text-[--text-secondary] max-w-2xl mb-12"
        >
          Each agent has a defined role, structured output, and visible status.
          Nothing happens in a hidden black box.
        </motion.p>

        {/* Agent Cards Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-12"
        >
          {agents.map((agent) => (
            <motion.div
              key={agent.number}
              variants={itemVariants}
              className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="font-mono text-xs text-[--text-muted]">
                  {agent.number}
                </span>
                <span className="flex items-center gap-1 text-xs text-[--color-success]">
                  <CheckCircle className="w-3 h-3" />
                  Success
                </span>
              </div>
              <h3 className="text-base font-semibold text-[--text-primary] mb-2">
                {agent.name}
              </h3>
              <p className="text-sm text-[--text-secondary] mb-4">
                {agent.description}
              </p>
              <div className="border-t border-[--border-subtle] pt-3">
                <span className="text-xs text-[--text-muted]">Output: </span>
                <span className="text-xs text-[--text-secondary]">
                  {agent.output}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Metrics Strip */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg px-6 py-4"
        >
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8">
            {metrics.map((metric, index) => (
              <div key={index} className="flex items-center gap-4">
                <span className="font-mono text-sm text-[--text-secondary] text-center">
                  {metric}
                </span>
                {index < metrics.length - 1 && (
                  <span className="hidden md:block w-px h-4 bg-[--border-default]" />
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
