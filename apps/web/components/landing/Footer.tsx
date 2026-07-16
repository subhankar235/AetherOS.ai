import { Globe, Mail, Rss } from 'lucide-react';

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'Triage', href: '#triage' },
      { label: 'Agents', href: '#agents' },
      { label: 'Security', href: '#security' },
      { label: 'Pricing', href: '#pricing' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#top' },
      { label: 'Blog', href: '#top' },
      { label: 'Careers', href: '#top' },
      { label: 'Contact', href: '#top' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '#top' },
      { label: 'API Reference', href: '#top' },
      { label: 'Status', href: '#top' },
      { label: 'Changelog', href: '#top' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy', href: '#top' },
      { label: 'Terms', href: '#top' },
      { label: 'Security', href: '#security' },
      { label: 'GDPR', href: '#top' },
    ],
  },
];

const socials = [
  { icon: Globe, label: 'Website', href: '#top' },
  { icon: Mail, label: 'Email', href: '#top' },
  { icon: Rss, label: 'Blog', href: '#top' },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-white/[0.06] py-16 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_100%_at_50%_100%,rgba(59,130,246,0.03),transparent)]" />

      <div className="relative max-w-7xl mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8 md:gap-12">
          {/* Brand */}
          <div className="col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="relative w-6 h-6">
                <div className="absolute inset-0 rounded-full bg-cobalt/30 blur-md" />
                <div className="relative w-6 h-6 rounded-full border border-cobalt/40 flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-cobalt" />
                </div>
              </div>
              <span className="text-stellar font-medium text-lg">Aether</span>
            </div>
            <p className="text-xs text-mercury/50 leading-relaxed max-w-[200px]">
              The AI Chief of Staff for your inbox. It watches, triages, and prepares — but only acts on your command.
            </p>
            <p className="text-[10px] text-mercury/30 font-mono uppercase tracking-widest mt-4">Authored by Intelligence</p>
          </div>

          {/* Link columns */}
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-[10px] font-mono uppercase tracking-widest text-mercury/40 mb-4">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a href={link.href} className="text-sm text-mercury/60 hover:text-stellar transition-colors duration-200">
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-white/[0.04] flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-mercury/40">© 2026 Aether. All rights reserved.</p>
          <div className="flex items-center gap-3">
            {socials.map((social) => (
              <a
                key={social.label}
                href={social.href}
                aria-label={social.label}
                className="w-8 h-8 rounded-full glass-card flex items-center justify-center text-mercury/50 hover:text-stellar hover:border-white/[0.15] transition-all duration-200"
              >
                <social.icon className="w-3.5 h-3.5" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}