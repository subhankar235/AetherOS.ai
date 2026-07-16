"use client";

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, HelpCircle } from 'lucide-react';

const faqs = [
  {
    q: 'Does the AI ever send emails without my permission?',
    a: 'Never. Every send, schedule, or payment requires your explicit approval through a confirmation step. The AI can draft, summarize, and prepare — but only you authorize an action. This is enforced at the API layer, not just the UI.',
  },
  {
    q: "How does it understand my company's context?",
    a: 'Upload your handbook, SOPs, pricing sheets, and policies to Company Memory. The AI grounds every reply in your actual documents using RAG, with inline citations to the source. If it can\'t find an answer, it says so — no fabrication.',
  },
  {
    q: 'Can I control everything by voice?',
    a: 'Yes. Every core workflow — search, read, reply, schedule — works via voice or text. The AI speaks back conversationally, never reciting raw data. Low-confidence transcriptions trigger a re-prompt for consequential commands.',
  },
  {
    q: 'Is my email data secure?',
    a: 'We use Google OAuth with scoped, incremental permissions — no passwords stored. Email metadata is encrypted at rest. Full email bodies are fetched on-demand from Gmail, never mirrored wholesale. OAuth tokens are encrypted with AES-256.',
  },
  {
    q: 'Which email providers are supported?',
    a: 'Gmail at launch, with Outlook on the roadmap. The agent architecture is provider-agnostic — new providers plug into the same Supervisor without re-engineering the core system.',
  },
  {
    q: 'What about suspicious or phishing emails?',
    a: 'The Inbox Agent flags suspicious content automatically with a "Suspicious" category. Email bodies are treated as untrusted data — any embedded instructions are never interpreted as commands to any agent, preventing prompt injection attacks.',
  },
];

export default function FAQ() {
  const [open, setOpen] = useState(0);

  return (
    <section id="faq" className="relative py-24 md:py-36 overflow-hidden">
      <div className="relative max-w-3xl mx-auto px-4 md:px-6">
        <div className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <HelpCircle className="w-3 h-3" /> Questions
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            Trust, verified.
          </motion.h2>
        </div>

        <div className="space-y-2">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className={`glass-card rounded-xl overflow-hidden transition-all duration-300 ${
                open === i ? 'border-white/[0.12]' : ''
              }`}
            >
              <button
                onClick={() => setOpen(open === i ? -1 : i)}
                className="w-full flex items-center justify-between gap-4 p-5 text-left"
              >
                <span className={`text-sm md:text-base font-medium ${open === i ? 'text-stellar' : 'text-mercury/80'}`}>
                  {faq.q}
                </span>
                <motion.div
                  animate={{ rotate: open === i ? 45 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex-shrink-0"
                >
                  <Plus className={`w-4 h-4 ${open === i ? 'text-cobalt-light' : 'text-mercury/40'}`} />
                </motion.div>
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  >
                    <p className="px-5 pb-5 text-sm text-mercury/60 leading-relaxed">{faq.a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}