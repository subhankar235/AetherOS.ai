"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import IntelligenceOrb from "./IntelligenceOrb";

const commands = [
  "Show me what came in from investors this week",
  "Reply to the investor one, keep it warm but concise",
  "Schedule this for Thursday afternoon",
  "What's our refund policy?",
  "Research Acme Corp before my 3pm",
];

function useTypewriter() {
  const [text, setText] = useState("");
  const [index, setIndex] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = commands[index];
    let timeout: ReturnType<typeof setTimeout>;

    if (!deleting && text.length < current.length) {
      timeout = setTimeout(() => setText(current.slice(0, text.length + 1)), 55);
    } else if (!deleting && text.length === current.length) {
      timeout = setTimeout(() => setDeleting(true), 2200);
    } else if (deleting && text.length > 0) {
      timeout = setTimeout(() => setText(current.slice(0, text.length - 1)), 28);
    } else {
      setDeleting(false);
      setIndex((prev) => (prev + 1) % commands.length);
    }

    return () => clearTimeout(timeout);
  }, [text, deleting, index]);

  return text;
}

export default function Hero() {
  const typed = useTypewriter();

  return (
    <section id="top" className="relative min-h-screen w-full flex flex-col items-center justify-center overflow-hidden bg-obsidian">
      <div className="absolute inset-0 z-0">
        <IntelligenceOrb />
      </div>

      <div
        className="absolute inset-0 z-0 opacity-20 bg-cover bg-center"
        style={{
          backgroundImage: "url(https://media.base44.com/images/public/6a58e6e082d55fbee00c55d1/c9e701674_generated_5782bc08.png)",
          maskImage: "radial-gradient(ellipse 60% 60% at 50% 50%, black 0%, transparent 70%)",
          WebkitMaskImage: "radial-gradient(ellipse 60% 60% at 50% 50%, black 0%, transparent 70%)",
        }}
      />

      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_100%_60%_at_50%_0%,transparent,rgba(5,5,5,0.8))]" />
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_100%_50%_at_50%_100%,rgba(5,5,5,0.6),transparent)]" />

      <div className="relative z-10 flex flex-col items-center text-center px-4 max-w-5xl mx-auto pt-20">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel mb-8"
        >
          <Sparkles className="w-3 h-3 text-cobalt-light" />
          <span className="text-xs font-mono uppercase tracking-widest text-mercury">Autonomously Refined</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-medium tracking-tighter text-stellar leading-[0.95]"
        >
          Your inbox,
          <br />
          <span className="text-gradient-stellar">autonomously refined.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="mt-8 text-base md:text-lg text-mercury max-w-xl mx-auto leading-relaxed font-light"
        >
          The first AI Chief of Staff that watches, triages, and prepares — but only acts on your command.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.85, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-2xl mx-auto mt-10 group"
        >
          <div className="absolute -inset-0.5 bg-cobalt/20 rounded-2xl blur-xl opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="relative glass-panel rounded-2xl p-2 flex items-center gap-2">
            <div className="flex-1 flex items-center px-4 py-3 min-h-[28px]">
              <span className="text-stellar/90 text-sm md:text-base text-left font-light">
                {typed}
                <span className="inline-block w-[2px] h-4 bg-cobalt-light ml-0.5 animate-pulse align-middle" />
              </span>
            </div>
            <a
              href="#cta"
              className="flex items-center gap-2 px-5 md:px-7 py-3 bg-stellar text-obsidian rounded-xl font-medium text-sm hover:bg-white transition-all duration-200 hover:shadow-[0_0_30px_-5px_rgba(249,250,251,0.4)] whitespace-nowrap"
            >
              <span className="hidden sm:inline">Command</span>
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.1 }}
          className="mt-6 flex items-center gap-6 text-xs text-mercury/60 font-mono"
        >
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-gate" /> No auto-send
          </span>
          <span className="hidden sm:flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cobalt" /> Voice or text
          </span>
          <span className="hidden sm:flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-mercury" /> Company-aware
          </span>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.4 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3"
      >
        <span className="text-[10px] uppercase tracking-[0.3em] text-mercury/50 font-mono">Scroll</span>
        <div className="w-px h-12 bg-gradient-to-b from-mercury/40 to-transparent" />
      </motion.div>
    </section>
  );
}
