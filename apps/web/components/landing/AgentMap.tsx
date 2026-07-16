"use client";

import { motion } from 'framer-motion';
import { Sparkles, Mail, CornerUpLeft, Calendar, Brain, Search, HelpCircle, Plus } from 'lucide-react';

const agents = [
  { name: 'Inbox', icon: Mail, angle: 0, desc: 'Fetch, summarize, categorize' },
  { name: 'Reply', icon: CornerUpLeft, angle: 60, desc: 'Draft grounded responses' },
  { name: 'Calendar', icon: Calendar, angle: 120, desc: 'Schedule with context' },
  { name: 'Knowledge', icon: Brain, angle: 180, desc: 'RAG over Company Memory' },
  { name: 'Research', icon: Search, angle: 240, desc: 'Company & competitor intel' },
  { name: 'Support', icon: HelpCircle, angle: 300, desc: 'In-app guidance' },
];

function getPos(angle: number, radius = 38) {
  const rad = (angle - 90) * (Math.PI / 180);
  return {
    x: 50 + radius * Math.cos(rad),
    y: 50 + radius * Math.sin(rad),
  };
}

export default function AgentMap() {
  return (
    <section id="agents" className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_50%_50%,rgba(59,130,246,0.03),transparent)]" />

      {/* Atmosphere image */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] opacity-[0.07] bg-cover bg-center rounded-full blur-3xl"
        style={{ backgroundImage: 'url(https://media.base44.com/images/public/6a58e6e082d55fbee00c55d1/cee682efe_generated_e95754cc.png)' }}
      />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="max-w-2xl mx-auto text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <Sparkles className="w-3 h-3" /> Agent Orchestration
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            One supervisor.
            <br />
            <span className="text-mercury/50">Six specialists.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-6 text-mercury text-base md:text-lg leading-relaxed font-light"
          >
            The Supervisor is always running. Every other agent spins up on demand for exactly one task, executes, and terminates. You never talk to an agent — you talk to the Supervisor.
          </motion.p>
        </div>

        {/* Diagram */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 1 }}
          className="relative w-full max-w-xl mx-auto aspect-square"
        >
          {/* SVG connection lines */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(59,130,246,0.3)" />
                <stop offset="100%" stopColor="rgba(59,130,246,0.05)" />
              </linearGradient>
            </defs>
            {agents.map((agent) => {
              const pos = getPos(agent.angle);
              return (
                <g key={agent.name}>
                  <line
                    x1="50" y1="50"
                    x2={pos.x} y2={pos.y}
                    stroke="rgba(59,130,246,0.12)"
                    strokeWidth="0.3"
                  />
                  <line
                    x1="50" y1="50"
                    x2={pos.x} y2={pos.y}
                    stroke="rgba(96,165,250,0.4)"
                    strokeWidth="0.4"
                    strokeDasharray="2 4"
                    className="animate-data-flow"
                  />
                </g>
              );
            })}
            {/* Outer ring */}
            <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.2" strokeDasharray="1 2" />
          </svg>

          {/* Supervisor node (center) */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
            <motion.div
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="relative"
            >
              <div className="absolute inset-0 bg-cobalt/20 blur-2xl rounded-full" />
              <div className="relative w-16 h-16 md:w-20 md:h-20 rounded-full glass-panel border-cobalt/40 flex items-center justify-center">
                <Sparkles className="w-6 h-6 md:w-7 md:h-7 text-cobalt-light" />
              </div>
              <div className="absolute -bottom-7 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="text-xs font-mono text-stellar">Supervisor</span>
              </div>
            </motion.div>
          </div>

          {/* Agent nodes */}
          {agents.map((agent, i) => {
            const pos = getPos(agent.angle);
            return (
              <motion.div
                key={agent.name}
                initial={{ opacity: 0, scale: 0.5 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                className="absolute z-10"
                style={{
                  top: `${pos.y}%`,
                  left: `${pos.x}%`,
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <motion.div
                  animate={{ y: [0, -5, 0] }}
                  transition={{ duration: 3 + i * 0.5, repeat: Infinity, ease: 'easeInOut' }}
                  className="flex flex-col items-center gap-2"
                >
                  <div className="relative">
                    <div className="absolute inset-0 bg-cobalt/10 blur-lg rounded-full" />
                    <div className="relative w-12 h-12 md:w-14 md:h-14 rounded-full glass-card border-white/[0.08] flex items-center justify-center group hover:border-cobalt/40 transition-all duration-300">
                      <agent.icon className="w-4 h-4 md:w-5 md:h-5 text-mercury group-hover:text-cobalt-light transition-colors" />
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[11px] md:text-xs font-medium text-stellar">{agent.name}</div>
                    <div className="text-[9px] md:text-[10px] text-mercury/40 font-mono hidden sm:block max-w-[100px]">{agent.desc}</div>
                  </div>
                </motion.div>
              </motion.div>
            );
          })}

          {/* Payment Agent (future) */}
          <div
            className="absolute z-10"
            style={{
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, calc(-50% + 130px))',
            }}
          >
            <div className="flex flex-col items-center gap-1">
              <div className="w-8 h-8 rounded-full border border-dashed border-white/[0.1] flex items-center justify-center">
                <Plus className="w-3 h-3 text-mercury/30" />
              </div>
              <span className="text-[9px] font-mono text-mercury/30">Payment · Soon</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}