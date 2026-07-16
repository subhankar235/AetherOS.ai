"use client";

import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

const triageItems = [
  { label: 'High priority', count: 18, color: 'cobalt' },
  { label: 'Meeting requests', count: 6, color: 'mercury' },
  { label: 'Awaiting reply', count: 11, color: 'mercury' },
  { label: 'Suspicious', count: 2, color: 'amber' },
];

const memoryDocs = [
  { doc: 'Fundraising_FAQ.pdf', score: 0.92 },
  { doc: 'Term_Sheet_Std_v4.docx', score: 0.87 },
  { doc: 'Pro-rata_Policy.md', score: 0.81 },
];

const waveformHeights = [12, 8, 16, 10, 20, 14, 8, 18, 10, 6, 12, 16, 8, 14, 10];

export default function CommandCentre() {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_30%,rgba(212,175,55,0.03),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/30">§ 85 — The Interface</span>
            <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/30 hidden sm:block">A single input. One agent at a time.</span>
          </div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            Not an inbox. A{' '}
            <span className="font-serif italic text-brass">command centre.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-6 text-mercury text-base md:text-lg leading-relaxed max-w-2xl font-light"
          >
            You never speak to a specific agent. You speak to Meridian. It decides — Inbox, Reply, Calendar, Knowledge, Research — and shows its work.
          </motion.p>
        </div>

        {/* Command Centre Window */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="relative"
        >
          <div className="absolute -inset-0.5 bg-gradient-to-b from-brass/10 via-transparent to-transparent rounded-2xl blur-md opacity-40" />

          <div className="relative rounded-2xl border border-white/[0.08] bg-obsidian-light overflow-hidden">
            {/* Top Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-white/[0.01]">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
              </div>
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-mercury/40">
                Meridian — Command Centre
              </span>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-gate animate-pulse" />
                <span className="text-[10px] font-mono text-emerald-gate/60">Listening</span>
              </div>
            </div>

            {/* Three-Column Grid */}
            <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-white/[0.06]">
              {/* Left Panel - Triage */}
              <div className="p-5 md:p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40">Today</span>
                  <span className="text-[10px] font-mono text-mercury/30">Triage</span>
                </div>

                <div className="mb-5">
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-medium tracking-tighter text-stellar">124</span>
                    <span className="text-xs text-mercury/50">emails</span>
                  </div>
                  <span className="text-[11px] font-mono text-cobalt-light/70">— 18 high</span>
                </div>

                <div className="space-y-2.5">
                  {triageItems.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          item.color === 'cobalt' ? 'bg-cobalt' :
                          item.color === 'amber' ? 'bg-amber-500/60' :
                          'bg-zinc-600'
                        }`} />
                        <span className="text-xs text-mercury/70">{item.label}</span>
                      </div>
                      <span className="text-xs font-mono text-mercury/50">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Center Panel - Drafting */}
              <div className="p-5 md:p-6 bg-white/[0.01]">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-brass/60">CH. 83 — Reply Agent — Drafting</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-brass animate-pulse-glow" />
                </div>

                <div className="mb-3">
                  <p className="text-[10px] font-mono text-mercury/40 mb-1">Subject</p>
                  <p className="text-sm text-stellar/90">Re: Series A term sheet — quick clarifications</p>
                </div>

                <div className="mb-4 text-[11px] font-mono text-mercury/40">
                  From: partner@northaxis.vc · thread 84
                </div>

                <div className="rounded-lg bg-obsidian/60 border border-white/[0.04] p-3 mb-4">
                  <p className="text-xs text-mercury/70 leading-relaxed">
                    Hi <span className="text-stellar/80">James</span>,<br /><br />
                    Thanks for the term sheet. After reviewing with Priya, we'd like to clarify the 1.5x participation cap — specifically whether it applies to the preferred return or the full liquidation amount.<br /><br />
                    Could we schedule a brief call Thursday afternoon to walk through this? Happy to send a calendar invite.<br /><br />
                    Best,<br />Daniel
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {['SHORTEN', 'WARMER', '+ CALENDAR LINK'].map((action) => (
                    <button key={action} className="px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider text-mercury/60 border border-white/[0.08] rounded hover:border-white/[0.15] hover:text-stellar transition-all">
                      {action}
                    </button>
                  ))}
                </div>

                <button className="w-full flex items-center justify-center gap-2 py-2.5 bg-brass text-obsidian rounded-lg text-xs font-medium uppercase tracking-widest hover:bg-brass-light transition-all">
                  <Check className="w-3.5 h-3.5" />
                  Approve · Send
                </button>

                <div className="flex items-center justify-center gap-1.5 mt-3">
                  <span className="text-brass/50">◆</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/30">
                    Approval Gate — send is blocked until you confirm
                  </span>
                </div>
              </div>

              {/* Right Panel - Context */}
              <div className="p-5 md:p-6">
                <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40">Context</span>

                <div className="mt-4 mb-5">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-mercury/30 mb-1.5">Thread summary</p>
                  <p className="text-xs text-mercury/60 leading-relaxed">
                    James from NorthAxis is negotiating Series A terms. He's pushing back on the participation cap and wants a call to discuss specifics before signing.
                  </p>
                </div>

                <div className="mb-5">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-mercury/30 mb-2">Company memory — retrieved</p>
                  <div className="space-y-1.5">
                    {memoryDocs.map((item) => (
                      <div key={item.doc} className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-mono text-mercury/50 truncate">{item.doc}</span>
                        <span className="text-[11px] font-mono text-cobalt-light/70 flex-shrink-0">{item.score}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[10px] font-mono uppercase tracking-wider text-mercury/30 mb-1.5">Playbook</p>
                  <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-brass/5 border border-brass/15">
                    <span className="text-[11px] font-mono text-brass/70">Investor · Warm-Concise</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Bar - Voice Input */}
            <div className="flex items-center gap-4 px-4 py-3 border-t border-white/[0.06] bg-white/[0.01]">
              <span className="text-xs text-mercury/60 italic flex-1 truncate">
                "Shorten it and schedule the call for Thursday afternoon."
              </span>

              <div className="flex items-center gap-0.5 h-4">
                {waveformHeights.map((h, i) => (
                  <motion.div
                    key={i}
                    animate={{ scaleY: [0.3, 1, 0.3] }}
                    transition={{
                      duration: 0.5 + (i % 3) * 0.15,
                      repeat: Infinity,
                      ease: 'easeInOut',
                      delay: i * 0.03,
                    }}
                    className="w-0.5 bg-brass/40 rounded-full origin-center"
                    style={{ height: `${h}px` }}
                  />
                ))}
              </div>

              <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40 whitespace-nowrap">
                Voice · EN
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}