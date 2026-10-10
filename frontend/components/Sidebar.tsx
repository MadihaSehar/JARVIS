"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/reconnaissance", label: "Reconnaissance" },
  { href: "/assets", label: "Asset Inventory" },
  { href: "/dns", label: "DNS and Subdomains" },
  { href: "/http-services", label: "HTTP Services" },
  { href: "/endpoints", label: "Endpoint Discovery" },
  { href: "/directories", label: "Directory Discovery" },
  { href: "/vulnerability-testing", label: "Vulnerability Testing" },
  { href: "/findings", label: "Findings" },
  { href: "/threat-intel", label: "Threat Intelligence" },
  { href: "/scan-history", label: "Scan History" },
  { href: "/ai-config", label: "AI Configuration" },
  { href: "/tool-integrations", label: "Tool Integrations" },
  { href: "/settings", label: "Settings" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 border-r border-panel-border bg-background-elevated flex flex-col">
      <div className="px-5 py-5 border-b border-panel-border">
        <div className="text-accent font-mono text-sm tracking-widest">J.A.R.V.I.S.</div>
        <div className="text-foreground-muted text-[11px] mt-1">
          Security Workstation
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-5 py-2 text-[13px] border-l-2 transition-colors ${
                active
                  ? "border-accent text-accent bg-panel"
                  : "border-transparent text-foreground-muted hover:text-foreground hover:bg-panel/50"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
