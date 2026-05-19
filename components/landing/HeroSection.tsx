"use client"

import { motion } from "framer-motion"
import {
  Inbox,
  Search,
  BarChart2,
  Lightbulb,
  Mail,
  CheckCircle,
  ArrowRight,
} from "lucide-react"

const agents = [
  {
    icon: Inbox,
    name: "Intake",
    description: "Validate & normalize",
  },
  {
    icon: Search,
    name: "Research",
    description: "Build company context",
  },
  {
    icon: BarChart2,
    name: "Qualify",
    description: "Score & prioritize",
  },
  {
    icon: Lightbulb,
    name: "Strategize",
    description: "Select sales angle",
  },
  {
    icon: Mail,
    name: "Draft",
    description: "Generate outreach",
  },
  {
    icon: CheckCircle,
    name: "Evaluate",
    description: "QA & flag risks",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.3,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
}

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center py-32 px-4 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 hero-glow" />
      <div className="absolute inset-0 dot-grid" />

      <div className="relative z-10 flex flex-col items-center max-w-5xl mx-auto">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-xs font-mono px-3 py-1 rounded-full border border-[--border-default] bg-[--bg-surface] text-[--text-muted] mb-8"
        >
          Multi-Agent AI Pipeline · Portfolio Edition
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl md:text-5xl font-semibold tracking-tight text-[--text-primary] max-w-3xl mx-auto text-center text-balance"
        >
          Research, qualify, and write personalized outreach — automatically.
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg text-[--text-secondary] max-w-xl mx-auto text-center mt-4 text-balance"
        >
          LeadForge turns a list of B2B leads into researched, scored, and
          review-ready sales opportunities using a traceable AI agent pipeline.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-3 mt-8"
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-6 py-2.5 rounded-md bg-[--accent-primary] text-white font-medium hover:brightness-110 transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)]"
          >
            Run Sample Demo
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-6 py-2.5 rounded-md border border-[--border-default] text-[--text-secondary] font-medium hover:bg-[--bg-elevated] transition-all"
          >
            View Architecture
          </motion.button>
        </motion.div>

        {/* Agent Pipeline Visual */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="mt-16 w-full max-w-5xl mx-auto px-4"
        >
          <div className="flex flex-wrap lg:flex-nowrap items-center justify-center gap-2 lg:gap-0">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.name}
                variants={itemVariants}
                className="flex items-center"
              >
                {/* Agent Card */}
                <div className="bg-[--bg-surface] border border-[--border-default] rounded-lg px-4 py-3 min-w-[140px]">
                  <div className="flex items-center gap-2 mb-1">
                    <agent.icon className="w-4 h-4 text-[--accent-primary]" />
                    <span className="font-semibold text-sm text-[--text-primary]">
                      {agent.name}
                    </span>
                    <span className="w-1.5 h-1.5 rounded-full bg-[--color-success] ml-auto" />
                  </div>
                  <p className="text-xs text-[--text-muted]">
                    {agent.description}
                  </p>
                </div>

                {/* Arrow connector */}
                {index < agents.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-[--border-default] mx-1 hidden lg:block flex-shrink-0" />
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
