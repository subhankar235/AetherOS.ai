"use client";

import { motion } from 'framer-motion';
import { TrendingDown, Edit3, ShieldX, Timer } from 'lucide-react';

const stats = [
  { value: '70%', suffix: '', label: 'Less triage time', sub: 'via automatic summarization & priority scoring', icon: TrendingDown },
  { value: '<20', suffix: '%', label: 'Edit distance on drafts', sub: 'replies grounded in your company knowledge', icon: Edit3 },
  { value: '0', suffix: '', label: 'Unauthorized actions', sub: 'every send, schedule & pay gated by approval', icon: ShieldX },
  { value: '3', suffix: ' min', label: 'To process an inbox', sub: 'what used to take 15 minutes, done in three', icon: Timer },
];

export default function Stats() {
  return (
    <section className="relative py-20 md:py-28 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_80%_at_50%_50%,rgba(59,130,246,0.04),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="relative glass-card rounded-2xl p-5 md:p-6 group hover:border-white/[0.12] transition-all duration-300"
            >
              <stat.icon className="w-4 h-4 text-cobalt-light/60 mb-4 group-hover:text-cobalt-light transition-colors" />
              <div className="flex items-baseline">
                <span className="text-4xl md:text-5xl font-medium tracking-tighter text-stellar">
                  {stat.value}
                </span>
                <span className="text-2xl md:text-3xl font-medium tracking-tighter text-mercury/50">
                  {stat.suffix}
                </span>
              </div>
              <div className="text-sm text-stellar/80 font-medium mt-2">{stat.label}</div>
              <div className="text-[11px] text-mercury/40 mt-1 leading-tight">{stat.sub}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}