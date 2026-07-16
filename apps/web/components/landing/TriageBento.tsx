"use client";

import { motion } from 'framer-motion';
import { ScanLine, Flag, FileText, Tag, Bell, AlertCircle } from 'lucide-react';

const scanEmails = [
  { sender: 'Marcus Webb', subject: 'Investor follow-up — Series A', priority: 'High', time: '2m', processed: true },
  { sender: 'Sarah Chen', subject: 'Re: Q3 budget review', priority: 'Medium', time: '5m', processed: true },
  { sender: 'Newsletter Bot', subject: 'Your weekly digest', priority: 'Low', time: '12m', processed: false },
  { sender: 'Alex Rivera', subject: 'Re: Partnership terms', priority: 'High', time: '18m', processed: false },
];

const priorityColors: Record<string, string> = {
  High: 'text-cobalt-light border-cobalt/30 bg-cobalt/10',
  Medium: 'text-mercury border-mercury/20 bg-mercury/5',
  Low: 'text-zinc-500 border-zinc-700 bg-zinc-800/30',
};

const cards = [
  {
    icon: Flag,
    title: 'Priority Scoring',
    desc: 'High, Medium, or Low — every email ranked by importance, not arrival time.',
    span: 'md:col-span-1 md:row-span-1',
    content: (
      <div className="flex flex-wrap gap-2">
        {['High', 'Medium', 'Low'].map((p) => (
          <span key={p} className={`px-2.5 py-1 text-[11px] font-mono rounded-md border ${priorityColors[p]}`}>
            {p}
          </span>
        ))}
      </div>
    ),
  },
  {
    icon: FileText,
    title: 'Smart Summaries',
    desc: 'Two-sentence summaries replace full reads. Know the gist without opening it.',
    span: 'md:col-span-1',
    content: (
      <div className="glass-card rounded-lg p-3 text-xs text-mercury/80 leading-relaxed">
        <span className="text-cobalt-light">Summary:</span> Investor confirms interest in Series A. Requests a call Thursday to discuss terms and valuation.
      </div>
    ),
  },
  {
    icon: Tag,
    title: 'Category Detection',
    desc: 'Auto-sorted by type.',
    span: 'md:col-span-1',
    content: (
      <div className="flex flex-wrap gap-1.5">
        {['Sales', 'Support', 'Internal', 'Newsletter', 'Finance'].map((c) => (
          <span key={c} className="px-2 py-0.5 text-[10px] font-mono text-mercury/70 rounded bg-white/[0.04] border border-white/[0.06]">
            {c}
          </span>
        ))}
      </div>
    ),
  },
  {
    icon: AlertCircle,
    title: 'Urgency Flag',
    desc: 'Time-sensitive items surfaced.',
    span: 'md:col-span-1',
    content: (
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-cobalt animate-pulse" />
        <span className="text-xs text-cobalt-light font-mono">Action needed today</span>
      </div>
    ),
  },
  {
    icon: Bell,
    title: 'Reply Required',
    desc: 'Never miss a response.',
    span: 'md:col-span-1',
    content: (
      <div className="flex items-center gap-2">
        <span className="px-2 py-0.5 text-[10px] font-mono text-emerald-gate rounded bg-emerald-gate/10 border border-emerald-gate/20">
          Reply needed
        </span>
        <span className="text-[10px] text-mercury/50 font-mono">3 pending</span>
      </div>
    ),
  },
];

export default function TriageBento() {
  return (
    <section id="triage" className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_30%_50%,rgba(59,130,246,0.04),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="max-w-2xl mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <ScanLine className="w-3 h-3" /> Automatic Intelligence
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            It watches. So you don't have to.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-6 text-mercury text-base md:text-lg leading-relaxed max-w-xl font-light"
          >
            The moment an email arrives, it's summarized, prioritized, and categorized — automatically. No reply, no schedule, no action. Just signal, ready when you are.
          </motion.p>
        </div>

        {/* Bento grid */}
        <div className="grid md:grid-cols-3 gap-3 md:gap-4">
          {/* Large card: Automatic Triage */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="md:col-span-2 md:row-span-2 relative glass-card rounded-2xl p-5 md:p-6 overflow-hidden group"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-stellar">Automatic Triage</h3>
                <p className="text-xs text-mercury/50 mt-0.5 font-mono">Live inbox processing</p>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-gate animate-pulse" />
                <span className="text-[10px] font-mono text-emerald-gate/70">ACTIVE</span>
              </div>
            </div>

            <div className="relative space-y-2">
              {/* Scan bar */}
              <div className="absolute left-0 right-0 h-16 bg-gradient-to-b from-transparent via-cobalt/10 to-transparent border-t border-cobalt/30 pointer-events-none animate-scan-line" />

              {scanEmails.map((email, i) => (
                <motion.div
                  key={email.sender}
                  initial={{ opacity: 0.3 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.15 }}
                  className={`flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-500 ${
                    email.processed
                      ? 'bg-white/[0.03] border-white/[0.08]'
                      : 'bg-white/[0.01] border-white/[0.04] opacity-50'
                  }`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${email.processed ? 'bg-cobalt' : 'bg-zinc-700'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-xs font-medium truncate ${email.processed ? 'text-stellar' : 'text-zinc-500'}`}>
                        {email.sender}
                      </span>
                      <span className="text-[10px] font-mono text-zinc-600 flex-shrink-0">{email.time}</span>
                    </div>
                    <p className={`text-xs truncate mt-0.5 ${email.processed ? 'text-mercury/70' : 'text-zinc-600'}`}>
                      {email.subject}
                    </p>
                  </div>
                  {email.processed && (
                    <span className={`px-2 py-0.5 text-[10px] font-mono rounded border flex-shrink-0 ${priorityColors[email.priority]}`}>
                      {email.priority}
                    </span>
                  )}
                </motion.div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/[0.06]">
              <p className="text-[11px] text-mercury/40 font-mono">
                ⛔ No reply drafted. No meeting scheduled. No action taken.
              </p>
            </div>
          </motion.div>

          {/* Smaller cards */}
          {cards.map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.6, delay: 0.1 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className={`${card.span} glass-card rounded-2xl p-5 hover:border-white/[0.12] transition-all duration-300 group`}
            >
              <card.icon className="w-4 h-4 text-cobalt-light mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="text-sm font-medium text-stellar mb-1">{card.title}</h3>
              <p className="text-xs text-mercury/50 mb-3 leading-relaxed">{card.desc}</p>
              {card.content}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}