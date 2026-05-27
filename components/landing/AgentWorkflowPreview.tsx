"use client"

import { motion } from "framer-motion"
import { CheckCircle } from "lucide-react"

const agents = [
  {
    number: "01",
    name: "Intake",
    role: "Validation & missing fields",
    description:
      "Normalizes submitted lead rows, flags missing context, and prepares records for the pipeline.",
    output: "Validation summary, missing-field warnings",
  },
  {
    number: "02",
    name: "Research",
    role: "Evidence & company context",
    description:
      "Builds company context from lead signals and curated knowledge. Evidence cards cite sources — never invented.",
    output: "Evidence cards, opportunity signals, company summary",
  },
  {
    number: "03",
    name: "Qualifier",
    role: "Fit score & priority",
    description:
      "Assigns a fit score (0–100) and priority tier based on ICP rules. Returns reasons for every score.",
    output: "Fit score, priority tier, qualification reasons",
  },
  {
    number: "04",
    name: "Strategist",
    role: "Sales angle & pain hypothesis",
    description:
      "Selects the best sales angle given research and qualification. Produces a pain hypothesis.",
    output: "Pain hypothesis, sales angle, core message",
  },
  {
    number: "05",
    name: "Email Drafter",
    role: "Reviewable outreach draft",
    description:
      "Generates a personalized outreach email grounded in evidence and strategy for human review.",
    output: "Subject line, email body, personalization notes",
  },
  {
    number: "06",
    name: "QA Evaluator",
    role: "QA score & review risks",
    description:
      "Scores output quality across multiple dimensions. Flags hallucination risk before human approval.",
    output: "QA scores, hallucination risk, review notes",
  },
]

const metrics = [
  "Six-agent workflow with visible agent trace",
  "Estimated ~$0.02–$0.05 per lead (when live models run)",
  "Replay/demo mode: $0 — saved outputs, no live agents",
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
    <section className="py-24 px-4 bg-[--surface]">
      <div className="max-w-5xl mx-auto">
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-xs font-mono uppercase tracking-widest text-[--accent-primary] mb-4"
        >
          Agent workflow
        </motion.p>

        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] max-w-2xl mb-4"
        >
          Six agents. One pipeline. Full traceability.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.15 }}
          className="text-[--text-secondary] max-w-2xl mb-12"
        >
          Intake → Research → Qualifier → Strategist → Email Drafter → QA
          Evaluator. Each agent has a defined role, structured output summary,
          and visible status. Nothing is presented as hidden reasoning.
        </motion.p>

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
              className="surface-card rounded-lg p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="font-mono text-xs text-[--text-muted]">
                  {agent.number}
                </span>
                <span className="flex items-center gap-1 text-xs text-[--color-success]">
                  <CheckCircle className="w-3 h-3" />
                  Defined role
                </span>
              </div>
              <h3 className="text-base font-semibold text-[--text-primary] mb-1">
                {agent.name}
              </h3>
              <p className="text-xs font-medium text-[--accent-primary] mb-2">
                {agent.role}
              </p>
              <p className="text-sm text-[--text-secondary] mb-4">
                {agent.description}
              </p>
              <div className="border-t border-[--border-subtle] pt-3">
                <span className="text-xs text-[--text-muted]">Output summary: </span>
                <span className="text-xs text-[--text-secondary]">
                  {agent.output}
                </span>
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="surface-card rounded-lg px-6 py-4"
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
