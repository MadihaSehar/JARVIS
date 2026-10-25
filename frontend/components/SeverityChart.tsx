"use client";

import { useState } from "react";
import { Finding } from "@/lib/api";

const SEVERITIES = [
  { key: "critical", label: "Critical", color: "var(--sev-critical)" },
  { key: "high", label: "High", color: "var(--sev-high)" },
  { key: "medium", label: "Medium", color: "var(--sev-medium)" },
  { key: "low", label: "Low", color: "var(--sev-low)" },
  { key: "info", label: "Info", color: "var(--sev-info)" },
] as const;

// Horizontal bars, one per severity. Each row is labelled with its name and
// count, so severity never relies on color alone.
export default function SeverityChart({ findings }: { findings: Finding[] }) {
  const [hovered, setHovered] = useState<string | null>(null);
  const counts: Record<string, number> = {};
  for (const f of findings) {
    const k = f.severity.toLowerCase();
    counts[k] = (counts[k] || 0) + 1;
  }
  const max = Math.max(1, ...SEVERITIES.map((s) => counts[s.key] || 0));
  const total = findings.length;

  return (
    <div className="space-y-2.5" role="table" aria-label="Findings by severity">
      {SEVERITIES.map((s) => {
        const n = counts[s.key] || 0;
        const pct = total ? Math.round((n / total) * 100) : 0;
        const dim = hovered !== null && hovered !== s.key;
        return (
          <div
            key={s.key}
            role="row"
            className="grid grid-cols-[72px_1fr_64px] items-center gap-3 text-[12px] cursor-default"
            onMouseEnter={() => setHovered(s.key)}
            onMouseLeave={() => setHovered(null)}
            title={`${s.label}: ${n} finding${n === 1 ? "" : "s"} (${pct}% of total)`}
          >
            <span role="cell" className="text-foreground-muted">{s.label}</span>
            <div role="cell" className="h-3 bg-background rounded-sm overflow-hidden">
              <div
                className="h-full rounded-r transition-opacity"
                style={{
                  width: `${(n / max) * 100}%`,
                  minWidth: n ? 4 : 0,
                  background: s.color,
                  opacity: dim ? 0.35 : 1,
                }}
              />
            </div>
            <span role="cell" className="text-right tabular-nums text-foreground">
              {n}
              <span className="text-foreground-muted ml-1.5">{pct}%</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}
