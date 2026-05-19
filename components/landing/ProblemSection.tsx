"use client"

import { motion } from "framer-motion"
import { Clock, Mail, Filter, EyeOff } from "lucide-react"

const problems = [
  {
    icon: Clock,
    title: "Hours lost per lead",
    body: "Researching a company before outreach takes 20-45 minutes. Manually. Per lead.",
  },
  {
    icon: Mail,
    title: "Generic emails, low replies",
    body: "Copy-paste outreach templates don't convert. Personalization at scale is unsolved.",
  },
  {
    icon: Filter,
    title: "No prioritization logic",
    body: "Which leads deserve attention now? Without a system, it's gut feeling.",
  },
  {
    icon: EyeOff,
    title: "Zero traceability",
    body: "Why was a lead skipped? Why was an email sent? No one can explain.",
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

export function ProblemSection() {
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
          The Problem
        </motion.p>

        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] max-w-2xl mb-12"
        >
          Manual prospecting is broken — and everyone knows it.
        </motion.h2>

        {/* Problem Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {problems.map((problem) => (
            <motion.div
              key={problem.title}
              variants={itemVariants}
              className="bg-[--bg-surface] border border-[--border-subtle] rounded-lg p-5"
            >
              <problem.icon className="w-5 h-5 text-[--accent-primary] mb-3" />
              <h3 className="text-sm font-semibold text-[--text-primary] mb-1">
                {problem.title}
              </h3>
              <p className="text-sm text-[--text-secondary]">{problem.body}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
