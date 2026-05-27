"use client"

import { motion } from "framer-motion"
import { Server, DollarSign, UserCheck } from "lucide-react"

const techStack = [
  "Plain-Python orchestration",
  "FastAPI",
  "Next.js",
  "TypeScript",
  "Tailwind CSS",
  "shadcn/ui",
  "Groq (opt-in API)",
  "SQLite",
  "In-memory telemetry",
  "Framer Motion",
]

const designDecisions = [
  {
    icon: Server,
    title: "Local-first",
    description:
      "Runs without external APIs in replay mode. No GPU required for demos.",
  },
  {
    icon: DollarSign,
    title: "Cost-controlled",
    description:
      "Every token is estimated before running. No surprise charges.",
  },
  {
    icon: UserCheck,
    title: "Human-in-the-loop",
    description:
      "The system never sends emails automatically. Human review is mandatory.",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
}

export function ArchitectureSection() {
  return (
    <section id="architecture" className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Label */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-xs font-mono uppercase tracking-widest text-[--accent-primary] mb-4"
        >
          Architecture
        </motion.p>

        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] max-w-2xl mb-12"
        >
          Built for auditability. Packaged for portfolio review.
        </motion.h2>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Left - Tech Stack */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h3 className="text-sm font-semibold text-[--text-primary] mb-4">
              Tech Stack
            </h3>
            <motion.div
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="flex flex-wrap gap-2"
            >
              {techStack.map((tech) => (
                <motion.span
                  key={tech}
                  variants={itemVariants}
                  className="px-3 py-1.5 text-sm font-mono text-[--text-secondary] border border-[--border-default] rounded-full bg-[--bg-surface]"
                >
                  {tech}
                </motion.span>
              ))}
            </motion.div>
          </motion.div>

          {/* Right - Design Decisions */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 }}
          >
            <h3 className="text-sm font-semibold text-[--text-primary] mb-4">
              Design Decisions
            </h3>
            <div className="space-y-4">
              {designDecisions.map((decision) => (
                <div key={decision.title} className="flex items-start gap-3">
                  <div className="mt-0.5 p-2 rounded-md bg-[--bg-surface] border border-[--border-subtle]">
                    <decision.icon className="w-4 h-4 text-[--accent-primary]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-[--text-primary]">
                      {decision.title}
                    </h4>
                    <p className="text-sm text-[--text-secondary]">
                      {decision.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
