"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';

const navLinks = [
  { label: 'Triage', href: '#triage' },
  { label: 'Agents', href: '#agents' },
  { label: 'Security', href: '#security' },
  { label: 'Pricing', href: '#pricing' },
];

export default function GhostNav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 80);
      const total = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(total > 0 ? (window.scrollY / total) * 100 : 0);
    };
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className="fixed top-0 left-0 right-0 z-50"
      >
        <div
          className={`absolute inset-0 transition-all duration-500 ${
            scrolled
              ? 'glass-panel border-b border-white/[0.06]'
              : 'bg-transparent border-b border-transparent'
          }`}
        />
        <div className="relative max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
          <a href="#top" className="flex items-center gap-2.5 group">
            <div className="relative w-6 h-6">
              <div className="absolute inset-0 rounded-full bg-cobalt/30 blur-md group-hover:bg-cobalt/50 transition-all" />
              <div className="relative w-6 h-6 rounded-full border border-cobalt/40 flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-cobalt animate-pulse-glow" />
              </div>
            </div>
            <span className="text-stellar font-medium tracking-tight text-lg">Aether</span>
          </a>

          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="px-4 py-2 text-sm text-mercury hover:text-stellar transition-colors duration-200"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <a
              href="/dashboard"
              className="hidden md:inline-flex items-center px-5 py-2 text-sm font-medium text-obsidian bg-stellar rounded-full hover:bg-white transition-all duration-200 hover:shadow-[0_0_30px_-5px_rgba(249,250,251,0.3)]"
            >
              Get Started
            </a>
            <button
              onClick={() => setMenuOpen(true)}
              className="md:hidden w-9 h-9 flex items-center justify-center text-stellar"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="relative h-px bg-transparent">
          <div
            className="h-full bg-gradient-to-r from-transparent via-cobalt to-transparent transition-all duration-150"
            style={{ width: `${progress}%` }}
          />
        </div>
      </motion.nav>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-[60] bg-obsidian/95 backdrop-blur-xl md:hidden flex flex-col"
          >
            <div className="flex items-center justify-between px-4 h-16">
              <span className="text-stellar font-medium text-lg">Aether</span>
              <button
                onClick={() => setMenuOpen(false)}
                className="w-9 h-9 flex items-center justify-center text-stellar"
                aria-label="Close menu"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 flex flex-col items-center justify-center gap-2">
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                  className="text-3xl font-medium tracking-tight text-stellar hover:text-cobalt transition-colors py-2"
                >
                  {link.label}
                </motion.a>
              ))}
              <motion.a
                href="/dashboard"
                onClick={() => setMenuOpen(false)}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + navLinks.length * 0.05 }}
                className="mt-6 px-8 py-3 text-base font-medium text-obsidian bg-stellar rounded-full"
              >
                Get Started
              </motion.a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}