"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ExternalLink } from "lucide-react"

export function FinalCTASection() {
  return (
    <section className="relative py-24 px-4 overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 cta-glow" />

      <div className="relative z-10 max-w-3xl mx-auto text-center">
        {/* Heading */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-3xl md:text-4xl font-semibold tracking-tight text-[--text-primary] mb-4"
        >
          See it work. No setup, no API key.
        </motion.h2>

        {/* Subtext */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-[--text-secondary] max-w-xl mx-auto mb-8"
        >
          The demo runs on pre-computed results — instant, free, and fully
          interactive. Explore every screen, every agent, every lead.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-3 justify-center"
        >
          <Link href="/demo">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 py-2.5 rounded-md bg-[--accent-primary] text-white font-medium hover:brightness-110 transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)]"
            >
              Run Sample Demo
            </motion.button>
          </Link>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-md border border-[--border-default] text-[--text-secondary] font-medium hover:bg-[--bg-elevated] transition-all"
          >
            View on GitHub
            <ExternalLink className="w-4 h-4" />
          </motion.button>
        </motion.div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="mt-12 text-xs text-[--text-muted]"
        >
          Portfolio Edition · Built with Next.js, FastAPI, TypeScript, and
          opt-in Groq · Not for production use
        </motion.p>
      </div>
    </section>
  )
}
