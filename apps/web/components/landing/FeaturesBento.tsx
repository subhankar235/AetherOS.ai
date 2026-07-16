"use client";

import { motion } from 'framer-motion';
import { Mic, Brain, BookMarked, Star, TrendingUp, Search, ArrowRight } from 'lucide-react';

const features = [
  {
    icon: Mic,
    title: 'Voice-First Control',
    desc: 'Speak naturally — "Read the high-priority ones," "Reply and make it warmer," "Schedule for Thursday." Every workflow works by voice or text.',
    span: 'md:col-span-2 md:row-span-2',
    big: true,
  },
  {
    icon: Brain,
    title: 'Company Memory',
    desc: 'Upload handbooks, SOPs, pricing. Replies grounded in your docs.',
    span: 'md:col-span-1',
  },
  {
    icon: BookMarked,
    title: 'Playbooks',
    desc: 'Structured templates for interviews, sales, support.',
    span: 'md:col-span-1',
  },
  {
    icon: Star,
    title: 'VIP Contacts',
    desc: 'Designated contacts always elevated to High priority.',
    span: 'md:col-span-1',
  },
  {
    icon: TrendingUp,
    title: 'Market Research',
    desc: 'Instant company reports with SWOT and competitors.',
    span: 'md:col-span-1',
  },
  {
    icon: Search,
    title: 'Natural Language Search',
    desc: '"Emails from investors last week" — no filters, just ask.',
    span: 'md:col-span-2',
  },
];

export default function FeaturesBento() {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_70%_30%,rgba(59,130,246,0.03),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="max-w-2xl mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <Mic className="w-3 h-3" /> Beyond Triage
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            Every workflow,
            <br />
            <span className="text-mercury/50">voice or text.</span>
          </motion.h2>
        </div>

        <div className="grid md:grid-cols-3 gap-3 md:gap-4 auto-rows-[minmax(140px,auto)]">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className={`${feature.span} group relative glass-card rounded-2xl p-5 md:p-6 hover:border-white/[0.12] transition-all duration-300 overflow-hidden`}
            >
              {/* Hover glow */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-[radial-gradient(ellipse_60%_60%_at_50%_0%,rgba(59,130,246,0.06),transparent)]" />

              <div className="relative">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg glass-card border-white/[0.06] flex items-center justify-center group-hover:border-cobalt/30 transition-all duration-300">
                    <feature.icon className="w-4 h-4 text-cobalt-light group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <h3 className={`font-medium text-stellar ${feature.big ? 'text-xl' : 'text-base'}`}>
                    {feature.title}
                  </h3>
                </div>

                <p className={`text-mercury/60 leading-relaxed ${feature.big ? 'text-sm md:text-base' : 'text-xs'}`}>
                  {feature.desc}
                </p>

                {feature.big && (
                  <div className="mt-6 space-y-2">
                    {[
                      { label: 'You', text: 'Read me the high-priority ones', color: 'mercury' },
                      { label: 'AI', text: 'You have 3. Marcus Webb, investor follow-up — wants to discuss Series A...', color: 'cobalt' },
                    ].map((msg, j) => (
                      <div key={j} className="flex items-start gap-3">
                        <span className={`text-[10px] font-mono mt-1 ${
                          msg.color === 'cobalt' ? 'text-cobalt-light' : 'text-mercury/40'
                        }`}>
                          {msg.label}
                        </span>
                        <p className={`text-xs leading-relaxed ${
                          msg.color === 'cobalt' ? 'text-stellar/80' : 'text-mercury/50'
                        }`}>
                          {msg.text}
                        </p>
                      </div>
                    ))}
                    <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-white/[0.04]">
                      <div className="flex gap-0.5 items-end h-3">
                        {[3, 5, 4, 6, 3, 5, 4].map((h, k) => (
                          <div
                            key={k}
                            className="w-0.5 bg-cobalt/40 rounded-full"
                            style={{ height: `${h * 2}px` }}
                          />
                        ))}
                      </div>
                      <span className="text-[10px] font-mono text-mercury/30">Listening...</span>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}