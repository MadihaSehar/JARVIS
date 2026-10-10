"use client";

import { useEffect, useMemo, useState } from "react";
import Panel from "@/components/Panel";
import SeverityBadge from "@/components/SeverityBadge";
import { api, Finding } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;

export default function FindingsPage() {
  const { currentScanId } = useScanContext();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!currentScanId) {
      setFindings([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const f = await api.getScanFindings(currentScanId!);
        if (!cancelled) setFindings(f);
      } catch {
        // ignore transient errors
      }
    }
    poll();
    const interval = setInterval(poll, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [currentScanId]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const f of findings) c[f.severity] = (c[f.severity] || 0) + 1;
    return c;
  }, [findings]);

  const visible = activeFilter ? findings.filter((f) => f.severity === activeFilter) : findings;

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Findings</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Evidence-based findings for the active scan. Click a finding to view its evidence.
        </p>
      </div>

      {!currentScanId ? (
        <Panel title="No Active Scan">
          <p className="text-foreground-muted text-[13px]">
            Start a scan from the Reconnaissance page to populate findings.
          </p>
        </Panel>
      ) : (
        <>
          <Panel title="Filter by Severity">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setActiveFilter(null)}
                className={`text-[11px] font-mono border rounded px-2 py-1 ${
                  activeFilter === null
                    ? "border-accent text-accent"
                    : "border-panel-border text-foreground-muted hover:text-foreground"
                }`}
              >
                ALL ({findings.length})
              </button>
              {SEVERITIES.map((sev) => (
                <button
                  key={sev}
                  onClick={() => setActiveFilter(sev)}
                  className={`text-[11px] font-mono border rounded px-2 py-1 uppercase ${
                    activeFilter === sev
                      ? "border-accent text-accent"
                      : "border-panel-border text-foreground-muted hover:text-foreground"
                  }`}
                >
                  {sev} ({counts[sev] || 0})
                </button>
              ))}
            </div>
          </Panel>

          <Panel title={`Findings (${visible.length})`}>
            {visible.length === 0 ? (
              <p className="text-foreground-muted text-[13px]">No findings match this filter.</p>
            ) : (
              <div className="space-y-3">
                {visible.map((f) => {
                  const isOpen = expanded.has(f.id);
                  return (
                    <div key={f.id} className="border border-panel-border rounded p-3">
                      <button
                        onClick={() => toggle(f.id)}
                        className="w-full flex items-center justify-between text-left"
                      >
                        <div className="flex items-center gap-2">
                          <SeverityBadge severity={f.severity} />
                          <span className="text-foreground font-mono text-[13px]">{f.category}</span>
                        </div>
                        <span className="text-foreground-muted text-[11px] font-mono">
                          {isOpen ? "collapse" : "expand"}
                        </span>
                      </button>
                      <p className="text-foreground-muted text-[12px] mt-2">{f.observation}</p>
                      {isOpen && (
                        <div className="mt-3 space-y-2 border-t border-panel-border pt-2">
                          <div>
                            <div className="text-[11px] text-foreground-muted font-mono">
                              CONFIDENCE
                            </div>
                            <div className="text-[13px] text-foreground">{f.confidence}</div>
                          </div>
                          {f.remediation && (
                            <div>
                              <div className="text-[11px] text-foreground-muted font-mono">
                                REMEDIATION
                              </div>
                              <div className="text-[13px] text-foreground">{f.remediation}</div>
                            </div>
                          )}
                          <div>
                            <div className="text-[11px] text-foreground-muted font-mono">
                              EVIDENCE
                            </div>
                            <pre className="text-[11px] text-foreground bg-background rounded p-2 overflow-x-auto">
                              {JSON.stringify(f.evidence, null, 2)}
                            </pre>
                          </div>
                          {f.human_review_required && (
                            <div className="text-warning text-[12px] font-mono">
                              Flagged for human review
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
