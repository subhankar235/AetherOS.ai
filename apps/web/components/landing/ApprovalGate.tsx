"use client";

import { useState, useRef, useEffect } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { Lock, Check, ShieldCheck, Send } from 'lucide-react';

const rules = [
  { icon: Check, text: 'Detection, drafting & preview — automatic once triggered', color: 'cobalt' },
  { icon: Lock, text: 'Sending, scheduling & paying — always behind the approval gate', color: 'emerald' },
  { icon: Send, text: 'Voice responses — never raw data, always conversational', color: 'mercury' },
];

export default function ApprovalGate() {
  const [approved, setApproved] = useState(false);
  const [maxDrag, setMaxDrag] = useState(260);
  const trackRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);

  useEffect(() => {
    const update = () => {
      if (trackRef.current) {
        setMaxDrag(Math.max(100, trackRef.current.offsetWidth - 56));
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const handleDragEnd = () => {
    if (x.get() > maxDrag * 0.8) {
      animate(x, maxDrag, { duration: 0.15 });
      setApproved(true);
      setTimeout(() => {
        animate(x, 0, { type: 'spring', stiffness: 300, damping: 30 });
        setApproved(false);
      }, 2500);
    } else {
      animate(x, 0, { type: 'spring', stiffness: 300, damping: 30 });
    }
  };

  const fillWidth = useTransform(x, [0, maxDrag], ['0%', '100%']);
  const fillOpacity = useTransform(x, [0, maxDrag * 0.5, maxDrag], [0, 0.3, 0.5]);
  const textOpacity = useTransform(x, [0, maxDrag * 0.3], [1, 0]);

  return (
    <section id="security" className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_50%,rgba(16,185,129,0.04),transparent)]" />

      {/* Atmosphere image */}
      <div
        className="absolute right-0 top-1/2 -translate-y-1/2 w-[500px] h-[500px] opacity-10 bg-cover bg-center rounded-full blur-3xl hidden lg:block"
        style={{ backgroundImage: 'url(https://media.base44.com/images/public/6a58e6e082d55fbee00c55d1/5865b55e9_generated_e61bb76c.png)' }}
      />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: text */}
          <div>
            <motion.span
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-emerald-gate/70 mb-4"
            >
              <ShieldCheck className="w-3 h-3" /> The Security Mandate
            </motion.span>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
            >
              Nothing happens
              <br />
              <span className="text-emerald-gate">without your word.</span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-mercury text-base md:text-lg leading-relaxed max-w-md font-light"
            >
              Most AI tools either automate too much or too little. Aether's differentiator is a strict boundary: only four things happen automatically — fetch, summarize, prioritize, categorize. Everything else requires your explicit approval.
            </motion.p>

            <div className="mt-10 space-y-4">
              {rules.map((rule, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -15 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: 0.3 + i * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    rule.color === 'emerald' ? 'bg-emerald-gate/10 border border-emerald-gate/20' : 'bg-cobalt/10 border border-cobalt/20'
                  }`}>
                    <rule.icon className={`w-3 h-3 ${
                      rule.color === 'emerald' ? 'text-emerald-gate' : 'text-cobalt-light'
                    }`} />
                  </div>
                  <p className="text-sm text-mercury/80 leading-relaxed">{rule.text}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Right: slide to approve */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            {/* Draft preview */}
            <div className="glass-card rounded-2xl p-5 mb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono uppercase tracking-widest text-mercury/40">Draft Preview</span>
                <span className="text-[10px] font-mono text-mercury/40">Reply Agent</span>
              </div>
              <div className="space-y-2">
                <div>
                  <span className="text-[10px] font-mono text-mercury/40">To:</span>{' '}
                  <span className="text-xs text-stellar/80">marcus@webbvc.com</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-mercury/40">Subject:</span>{' '}
                  <span className="text-xs text-stellar/80">Re: Investor follow-up — Series A</span>
                </div>
                <div className="pt-2 border-t border-white/[0.06]">
                  <p className="text-xs text-mercury/70 leading-relaxed">
                    Hi Marcus, thanks for the note. I'd love to discuss the Series A in more detail.
                    <span className="text-cobalt-light/60"> Grounded in: Fundraising FAQ v3.2</span>
                    <br /><br />
                    Are you available Thursday afternoon for a 30-minute call? I'll send a calendar invite once you confirm.
                    <br /><br />
                    Best,<br />Daniel
                  </p>
                </div>
              </div>
            </div>

            {/* Slide to approve track */}
            <div
              ref={trackRef}
              className={`relative h-14 rounded-full overflow-hidden border transition-all duration-500 ${
                approved
                  ? 'bg-emerald-gate/15 border-emerald-gate/40 glow-emerald'
                  : 'glass-card border-white/[0.08]'
              }`}
            >
              <motion.div
                style={{ width: fillWidth, opacity: fillOpacity }}
                className="absolute inset-y-0 left-0 bg-emerald-gate"
              />
              <motion.div
                style={{ opacity: textOpacity }}
                className="absolute inset-0 flex items-center justify-center pointer-events-none"
              >
                <span className="text-xs font-mono uppercase tracking-widest text-mercury/60 flex items-center gap-2">
                  <Lock className="w-3 h-3" /> Slide to approve send
                </span>
              </motion.div>
              {approved && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <span className="text-xs font-mono uppercase tracking-widest text-emerald-gate flex items-center gap-2">
                    <Check className="w-3 h-3" /> Approved — email sent
                  </span>
                </motion.div>
              )}
              <motion.div
                drag="x"
                dragConstraints={{ left: 0, right: maxDrag }}
                dragElastic={0}
                dragMomentum={false}
                onDragEnd={handleDragEnd}
                style={{ x }}
                className="absolute top-1/2 left-1 -translate-y-1/2 w-12 h-12 rounded-full flex items-center justify-center cursor-grab active:cursor-grabbing z-10"
                whileTap={{ scale: 0.95 }}
              >
                <div className={`absolute inset-0 rounded-full transition-all duration-500 ${
                  approved ? 'bg-emerald-gate' : 'bg-stellar'
                }`} />
                <div className={`absolute inset-0 rounded-full blur-md transition-all duration-500 ${
                  approved ? 'bg-emerald-gate/40' : 'bg-stellar/30'
                }`} />
                <div className="relative">
                  {approved ? (
                    <Check className="w-5 h-5 text-obsidian" />
                  ) : (
                    <Send className="w-4 h-4 text-obsidian" />
                  )}
                </div>
              </motion.div>
            </div>

            <p className="mt-4 text-[11px] text-mercury/40 font-mono text-center">
              Every consequential action passes through this gate. No exceptions.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}