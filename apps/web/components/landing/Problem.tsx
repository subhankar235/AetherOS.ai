"use client";

import { motion } from "framer-motion";
import { Inbox, Clock, AlertCircle } from "lucide-react";

interface Email {
  sender: string;
  subject: string;
  time: string;
  top: string;
  left: string;
  delay: number;
  highlight: boolean;
}

const stats = [
  { value: "100–150", label: "emails per day" },
  { value: "2–3 hrs", label: "spent triaging" },
  { value: "0", label: "built-in prioritization" },
];

const emails: Email[] = [
  { sender: "Newsletter Bot", subject: "Your weekly digest is here", time: "2m", top: "4%", left: "2%", delay: 0, highlight: false },
  { sender: "Sarah Chen", subject: "Re: Q3 budget review", time: "5m", top: "8%", left: "52%", delay: 0.3, highlight: false },
  { sender: "Stripe", subject: "Invoice #2847 paid", time: "12m", top: "28%", left: "8%", delay: 0.6, highlight: false },
  { sender: "Marcus Webb", subject: "Investor follow-up — Series A", time: "18m", top: "32%", left: "58%", delay: 0.9, highlight: true },
  { sender: "GitHub", subject: "12 pull requests need review", time: "25m", top: "55%", left: "4%", delay: 1.2, highlight: false },
  { sender: "HR Dept", subject: "Benefits enrollment opens", time: "33m", top: "60%", left: "55%", delay: 1.5, highlight: false },
  { sender: "Calendly", subject: "New booking: 30 min demo", time: "41m", top: "78%", left: "12%", delay: 1.8, highlight: false },
  { sender: "Alex Rivera", subject: "Re: Partnership terms", time: "48m", top: "80%", left: "52%", delay: 2.1, highlight: false },
];

function FloatingEmail({ email }: { email: Email }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay: email.delay * 0.3 }}
      className={`absolute w-[200px] sm:w-[240px] rounded-xl p-3 border transition-all ${
        email.highlight
          ? "glass-panel border-cobalt/40 glow-cobalt"
          : "bg-white/[0.02] border-white/[0.05] backdrop-blur-sm"
      }`}
      style={{ top: email.top, left: email.left }}
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 4 + email.delay, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${email.highlight ? "bg-cobalt" : "bg-zinc-600"}`} />
            <span className={`text-xs font-medium truncate ${email.highlight ? "text-stellar" : "text-zinc-400"}`}>
              {email.sender}
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-600">{email.time}</span>
        </div>
        <p className={`text-xs truncate ${email.highlight ? "text-stellar/90" : "text-zinc-500"}`}>
          {email.subject}
        </p>
      </motion.div>
    </motion.div>
  );
}

export default function Problem() {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_70%_50%,rgba(59,130,246,0.04),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-16 lg:gap-8 items-center">
          <div>
            <motion.span
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-6"
            >
              <AlertCircle className="w-3 h-3" /> The Problem
            </motion.span>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
            >
              150 emails a day.
              <br />
              <span className="text-mercury/50">Zero signal.</span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-mercury text-base md:text-lg leading-relaxed max-w-md font-light"
            >
              The average professional drowns in a hundred-plus emails daily. Inboxes sort by time, not importance. Every morning starts with manual triage — the same repetitive, soul-draining work, every single day.
            </motion.p>

            <div className="mt-10 grid grid-cols-3 gap-4 max-w-md">
              {stats.map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: 0.3 + i * 0.1 }}
                >
                  <div className="text-2xl md:text-3xl font-medium tracking-tight text-stellar">{stat.value}</div>
                  <div className="text-[11px] text-mercury/50 mt-1 leading-tight">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="relative h-[420px] sm:h-[500px] hidden lg:block">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-cobalt/20 blur-2xl rounded-full" />
                <div className="relative w-14 h-14 rounded-full glass-panel border-cobalt/30 flex items-center justify-center">
                  <Inbox className="w-6 h-6 text-cobalt-light" />
                </div>
              </div>
            </motion.div>
            {emails.map((email) => (
              <FloatingEmail key={email.sender} email={email} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
