"use client";

import { motion } from 'framer-motion';
import { Check, CreditCard } from 'lucide-react';

const tiers = [
  {
    name: 'Starter',
    price: '$0',
    period: '/mo',
    desc: 'For individuals getting started',
    features: [
      'Gmail + Calendar sync',
      'Automatic triage & summaries',
      '50 voice commands / month',
      '1 GB Company Memory',
      'Community support',
    ],
    highlight: false,
  },
  {
    name: 'Professional',
    price: '$29',
    period: '/mo',
    desc: 'For power users and founders',
    features: [
      'Everything in Starter',
      'Unlimited voice commands',
      '50 GB Company Memory',
      'Playbooks & VIP contacts',
      'Market Research agent',
      'Priority support',
    ],
    highlight: true,
  },
  {
    name: 'Team',
    price: '$99',
    period: '/mo',
    desc: 'For teams and workspaces',
    features: [
      'Everything in Professional',
      'Shared Company Memory',
      'Role-based access control',
      'Full audit logs',
      'Admin dashboard',
      'Dedicated support',
    ],
    highlight: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="relative py-24 md:py-36 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_50%,rgba(59,130,246,0.03),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="max-w-2xl mx-auto text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-mercury/60 mb-4"
          >
            <CreditCard className="w-3 h-3" /> Pricing
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-5xl md:text-6xl font-medium tracking-tighter text-stellar leading-[1.05]"
          >
            Start free.
            <br />
            <span className="text-mercury/50">Scale when ready.</span>
          </motion.h2>
        </div>

        <div className="grid md:grid-cols-3 gap-4 md:gap-6">
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
              className={`relative rounded-2xl p-6 md:p-8 ${
                tier.highlight
                  ? 'glass-panel border-cobalt/30 glow-cobalt'
                  : 'glass-card'
              }`}
            >
              {tier.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-obsidian bg-stellar rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-medium text-stellar">{tier.name}</h3>
                <p className="text-xs text-mercury/50 mt-1">{tier.desc}</p>
              </div>

              <div className="flex items-baseline mb-6">
                <span className="text-4xl font-medium tracking-tighter text-stellar">{tier.price}</span>
                <span className="text-sm text-mercury/50 ml-1">{tier.period}</span>
              </div>

              <a
                href="#cta"
                className={`block w-full text-center py-3 rounded-xl text-sm font-medium transition-all duration-200 mb-6 ${
                  tier.highlight
                    ? 'bg-stellar text-obsidian hover:bg-white hover:shadow-[0_0_30px_-5px_rgba(249,250,251,0.3)]'
                    : 'glass-card text-stellar hover:border-white/[0.15]'
                }`}
              >
                {tier.price === '$0' ? 'Get Started' : 'Start Free Trial'}
              </a>

              <ul className="space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <Check className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${
                      tier.highlight ? 'text-cobalt-light' : 'text-emerald-gate'
                    }`} />
                    <span className="text-xs text-mercury/70 leading-relaxed">{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}