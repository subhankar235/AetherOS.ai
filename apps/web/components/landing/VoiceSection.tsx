"use client";

import { motion } from 'framer-motion';
import { Mic } from 'lucide-react';

const dialogue = [
  {
    speaker: 'YOU',
    text: 'Read me the high-priority ones.',
    italic: true,
  },
  {
    speaker: 'MERIDIAN',
    text: "You've got three that look important today — the term sheet from Northaxis, a note from Anna at Meta, and the customer with the refund question. Want me to open the first?",
    italic: false,
  },
  {
    speaker: 'YOU',
    text: 'Reply to the investor — warm but concise.',
    italic: true,
  },
  {
    speaker: 'MERIDIAN',
    text: 'Draft is ready. It confirms Thursday at 3, keeps the pro-rata line, and adds a Meet link. Say the word to send.',
    italic: false,
  },
];

const waveformBars = [8, 14, 22, 10, 30, 18, 36, 12, 28, 16, 40, 20, 10, 34, 14, 26, 8, 32, 18, 24, 12, 38, 16, 20, 10, 28, 14, 22, 8, 30];

export default function VoiceSection() {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden bg-obsidian">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_75%_50%,rgba(212,180,106,0.06),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Text + Transcript */}
          <div>
            <motion.span
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-mercury/40 mb-6"
            >
              <Mic className="w-3 h-3" /> Voice & Tone
            </motion.span>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="text-4xl sm:text-5xl md:text-6xl font-serif tracking-tight text-stellar leading-[1.1]"
            >
              It sounds like a{' '}
              <span className="text-brass-light italic">person.</span>{' '}
              Because it was written to.
            </motion.h2>

            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-6 text-mercury text-sm md:text-base leading-relaxed max-w-lg font-serif"
            >
              Voice responses never read raw data aloud. Meridian rewrites structured results into natural spoken language and adapts tone —{' '}
              <span className="text-brass-light italic">warm on triage, careful on approvals, calm on suspicion.</span>
            </motion.p>

            {/* Transcript */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="mt-10 space-y-5"
            >
              {dialogue.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
                  className="flex gap-4"
                >
                  <div className="flex-shrink-0 w-20 pt-0.5">
                    <span className={`text-[10px] font-mono uppercase tracking-widest ${
                      msg.speaker === 'YOU' ? 'text-mercury/40' : 'text-brass/60'
                    }`}>
                      {msg.speaker}
                    </span>
                  </div>
                  <p className={`flex-1 font-serif text-sm md:text-[15px] leading-relaxed ${
                    msg.italic ? 'italic text-stellar' : 'text-mercury/80'
                  }`}>
                    {msg.text}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>

          {/* Right: Gold Orb + Waveform */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 1, delay: 0.2 }}
            className="relative flex flex-col items-center justify-center"
          >
            {/* Orb */}
            <div className="relative w-[280px] h-[280px] sm:w-[360px] sm:h-[360px] md:w-[420px] md:h-[420px]">
              {/* Outer glow */}
              <div className="absolute inset-0 rounded-full bg-brass/10 blur-[80px] animate-breath" />
              <div className="absolute -inset-8 rounded-full bg-brass/5 blur-[60px]" />

              {/* Sphere */}
              <motion.div
                animate={{ scale: [1, 1.02, 1] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute inset-0 rounded-full"
                style={{
                  background: 'radial-gradient(circle at 35% 35%, #F5D88A 0%, #D4B46A 25%, #B08A3E 50%, #6B562B 80%, #3D2F15 100%)',
                  boxShadow: 'inset -20px -20px 60px rgba(61,47,21,0.6), inset 10px 10px 40px rgba(245,216,138,0.3), 0 0 80px -10px rgba(212,180,106,0.3)',
                }}
              >
                {/* Highlight */}
                <div
                  className="absolute top-[15%] left-[20%] w-[35%] h-[35%] rounded-full"
                  style={{
                    background: 'radial-gradient(ellipse at center, rgba(255,248,230,0.5) 0%, transparent 70%)',
                  }}
                />
                {/* Inner glow ring */}
                <div
                  className="absolute inset-[30%] rounded-full opacity-30"
                  style={{
                    background: 'radial-gradient(circle, rgba(255,235,180,0.4) 0%, transparent 60%)',
                  }}
                />
              </motion.div>
            </div>

            {/* Waveform */}
            <div className="flex items-center justify-center gap-1 h-12 mt-8">
              {waveformBars.map((h, i) => (
                <motion.div
                  key={i}
                  animate={{ scaleY: [0.2, 1, 0.3, 0.8, 0.2] }}
                  transition={{
                    duration: 0.8 + (i % 4) * 0.15,
                    repeat: Infinity,
                    ease: 'easeInOut',
                    delay: i * 0.04,
                  }}
                  className="w-1 rounded-full origin-center"
                  style={{
                    height: `${h}px`,
                    background: 'linear-gradient(to top, #6B562B, #D4B46A)',
                  }}
                />
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}