"use client";

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function FinalCTA() {
  return (
    <section id="cta" className="relative py-32 md:py-48 overflow-hidden">
      {/* Background — cobalt to emerald "peace of mind" transition */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-cobalt/[0.08] rounded-full blur-[150px] animate-breath" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-gate/[0.05] rounded-full blur-[120px]" />
      </div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_100%_60%_at_50%_50%,transparent,rgba(5,5,5,0.7))]" />

      <div className="relative max-w-4xl mx-auto px-4 md:px-6 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel mb-8"
        >
          <Sparkles className="w-3 h-3 text-cobalt-light" />
          <span className="text-xs font-mono uppercase tracking-widest text-mercury">Authored by Intelligence</span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl sm:text-6xl md:text-8xl font-medium tracking-tighter text-stellar leading-[0.95]"
        >
          Your inbox is
          <br />
          <span className="text-gradient-stellar">waiting.</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-8 text-mercury text-base md:text-lg max-w-xl mx-auto leading-relaxed font-light"
        >
          Connect your Gmail in 60 seconds. Watch the noise fade. Start commanding your inbox — by voice or text.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="#top"
            className="group relative flex items-center gap-2 px-8 py-4 bg-stellar text-obsidian rounded-full font-medium hover:bg-white transition-all duration-200 hover:shadow-[0_0_40px_-5px_rgba(249,250,251,0.4)]"
          >
            Start Free
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </a>
          <span className="text-xs text-mercury/40 font-mono">No credit card · Cancel anytime</span>
        </motion.div>
      </div>
    </section>
  );
}