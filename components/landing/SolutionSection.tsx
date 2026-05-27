"use client"

import { motion } from "framer-motion"
import { Database, BarChart2, Shield } from "lucide-react"

const solutions = [
  {
    icon: Database,
    title: "Evidence-grounded research",
    body: "Every lead gets company context built from deterministic demo signals and curated knowledge, not hallucinated guesses. Evidence cards show what supported the recommendation.",
  },
  {
    icon: BarChart2,
    title: "Explainable qualification",
    body: "Fit scores (0-100) come with specific reasons. High / Medium / Low priority tiers with ICP match logic. No black-box scoring.",
  },
  {
    icon: Shield,
    title: "Human review, always",
    body: "The system researches, qualifies, drafts, and evaluates. But you decide. Every lead passes through a mandatory human review before any action.",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

export function SolutionSection() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Label */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-xs font-mono uppercase tracking-widest text-[--accent-primary] mb-4"
        >
          The Solution
        </motion.p>

        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] max-w-2xl mb-12"
        >
          A structured pipeline that works the way a great analyst would.
        </motion.h2>

        {/* Solution Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {solutions.map((solution) => (
            <motion.div
              key={solution.title}
              variants={itemVariants}
              className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5"
            >
              <solution.icon className="w-5 h-5 text-[--accent-primary] mb-3" />
              <h3 className="text-sm font-semibold text-[--text-primary] mb-1">
                {solution.title}
              </h3>
              <p className="text-sm text-[--text-secondary]">{solution.body}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
