"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { to: "/settings", label: "General" },
  { to: "/settings/integrations", label: "Integrations" },
  { to: "/settings/voice", label: "Voice & tone" },
  { to: "/settings/security", label: "Security" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Configure Aether and its agents.</p>
      </div>
      <div className="flex gap-1 border-b border-border">
        {tabs.map((t) => {
          const active = pathname === t.to;
          return (
            <Link
              key={t.to}
              href={t.to}
              className={`border-b-2 px-3 py-2 text-sm ${
                active
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </div>
      {children}
    </div>
  );
}
