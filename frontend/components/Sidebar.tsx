"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_GROUPS = [
  {
    label: "Command",
    items: [
      { href: "/", label: "Overview" },
      { href: "/reconnaissance", label: "Reconnaissance" },
      { href: "/scan-history", label: "Scan History" },
    ],
  },
  {
    label: "Attack surface",
    items: [
      { href: "/assets", label: "Asset Inventory" },
      { href: "/dns", label: "DNS and Subdomains" },
      { href: "/http-services", label: "HTTP Services" },
      { href: "/endpoints", label: "Endpoint Discovery" },
      { href: "/directories", label: "Directory Discovery" },
    ],
  },
  {
    label: "Testing",
    items: [
      { href: "/vulnerability-testing", label: "Vulnerability Testing" },
      { href: "/findings", label: "Findings" },
      { href: "/threat-intel", label: "Threat Intelligence" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/ai-config", label: "AI Configuration" },
      { href: "/tool-integrations", label: "Tool Integrations" },
      { href: "/settings", label: "Settings" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 border-r border-panel-border bg-background-elevated flex flex-col">
      <div className="px-5 py-5 border-b border-panel-border">
        <div className="text-accent font-mono text-base tracking-[0.3em] drop-shadow-[0_0_8px_rgba(34,211,238,0.45)]">J.A.R.V.I.S.</div>
        <div className="text-foreground-muted text-[11px] mt-1">
          Security Workstation
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-3">
            <div className="px-5 pt-2 pb-1 text-[10px] font-mono tracking-widest uppercase text-foreground-muted/70">
              {group.label}
            </div>
            {group.items.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block px-5 py-1.5 text-[13px] border-l-2 transition-colors ${
                    active
                      ? "border-accent text-accent bg-accent/10"
                      : "border-transparent text-foreground-muted hover:text-foreground hover:bg-panel/50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="px-5 py-3 border-t border-panel-border text-[10px] font-mono text-foreground-muted">
        local-first &middot; scope-enforced
      </div>
    </aside>
  );
}
