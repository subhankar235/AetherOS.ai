"use client";

import { motion } from "framer-motion";
import { Mail, Brain, Tag, Flag, Activity, Ban, Mic, Cpu, Zap, Eye, Lock, Check, FileText, Layers, type LucideIcon } from "lucide-react";

interface PathStepData {
  icon: LucideIcon;
  title: string;
  desc: string;
  stop?: boolean;
  gate?: boolean;
}

const pathA: PathStepData[] = [
  { icon: Mail, title: "New email arrives", desc: "Gmail push notification fires" },
  { icon: Brain, title: "AI analyzes content", desc: "Structured generation via GPT-5.5" },
  { icon: Tag, title: "Categorized & summarized", desc: "Summary, category, priority, urgency" },
  { icon: Flag, title: "Priority assigned", desc: "High / Medium / Low scoring" },
  { icon: Activity, title: "Dashboard updates live", desc: "WebSocket push, no refresh needed" },
  { icon: Ban, title: "Stops — no action taken", desc: "No reply, no schedule, no payment. Ever.", stop: true },
];

const pathB: PathStepData[] = [
  { icon: Mic, title: "You speak or type", desc: "Captured as text (STT if voice)" },
  { icon: Cpu, title: "Supervisor routes intent", desc: "Classifies & resolves context" },
  { icon: Zap, title: "Agent activates on demand", desc: "One specialist per task" },
  { icon: Eye, title: "Preview rendered", desc: "Draft, meeting, or report shown" },
  { icon: Lock, title: "Approval gate", desc: "User confirms before any action", gate: true },
  { icon: Check, title: "Action executes", desc: "Gmail / Calendar / Payment API" },
  { icon: FileText, title: "Audit logged", desc: "Actor, payload, timestamp recorded" },
];

function PathStep({ step, index, isLast }: { step: PathStepData; index: number; isLast: boolean }) {
  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {!isLast && (
        <div className="absolute left-[15px] top-8 bottom-0 w-px bg-gradient-to-b from-white/[0.08] to-transparent" />
      )}

      <div className={`relative w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border ${
        step.stop
          ? "bg-white/[0.02] border-white/[0.06]"
          : step.gate
          ? "bg-emerald-gate/10 border-emerald-gate/30"
          : "bg-cobalt/5 border-cobalt/20"
      }`}>
        <step.icon className={`w-3.5 h-3.5 ${
          step.stop ? "text-mercury/40" : step.gate ? "text-emerald-gate" : "text-cobalt-light"
        }`} />
        {step.gate && (
          <div className="absolute inset-0 rounded-full border border-emerald-gate/20 animate-pulse-glow" />
        )}
      </div>

      <div className="flex-1 pt-0.5">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-mercury/30">{String(index + 1).padStart(2, "0")}</span>
          <h4 className={`text-sm font-medium ${step.stop ? "text-mercury/50" : "text-stellar"}`}>
            {step.title}
          </h4>
        </div>
        <p className="text-xs text-mercury/40 mt-0.5">{step.desc}</p>
      </div>
    </div>
  );
}

export default function Workflow() {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_50%,rgba(59,130,246,0.02),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="max-w-2xl mx-auto text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <Layers className="w-3 h-3" /> Two Paths
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            Automatic where it&apos;s safe.
            <br />
            <span className="text-mercury/50">Manual where it matters.</span>
          </motion.h2>
        </div>

        <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="glass-card rounded-2xl p-6 md:p-8"
          >
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.06]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40">Path A</span>
                <h3 className="text-lg font-medium text-stellar mt-1">Automatic · Silent</h3>
              </div>
              <span className="px-2.5 py-1 text-[10px] font-mono rounded-md bg-cobalt/10 border border-cobalt/20 text-cobalt-light">
                Background
              </span>
            </div>
            <div>
              {pathA.map((step, i) => (
                <PathStep key={i} step={step} index={i} isLast={i === pathA.length - 1} />
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="glass-card rounded-2xl p-6 md:p-8"
          >
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.06]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40">Path B</span>
                <h3 className="text-lg font-medium text-stellar mt-1">Command-Driven</h3>
              </div>
              <span className="px-2.5 py-1 text-[10px] font-mono rounded-md bg-emerald-gate/10 border border-emerald-gate/20 text-emerald-gate">
                User-initiated
              </span>
            </div>
            <div>
              {pathB.map((step, i) => (
                <PathStep key={i} step={step} index={i} isLast={i === pathB.length - 1} />
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
