"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, Scan } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function ScanHistoryPage() {
  const { currentScanId, setCurrentScanId } = useScanContext();
  const [scans, setScans] = useState<Scan[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const s = await api.listScans();
        if (!cancelled) setScans(s);
      } catch {
        // ignore transient errors
      }
    }
    poll();
    const interval = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Scan History</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Every scan ever run. Select one to make it the active scan across the app.
        </p>
      </div>

      <Panel title={`All Scans (${scans.length})`}>
        {scans.length === 0 ? (
          <p className="text-foreground-muted text-[13px]">No scans yet.</p>
        ) : (
          <table className="w-full text-[13px] font-mono">
            <thead>
              <tr className="text-foreground-muted text-left border-b border-panel-border">
                <th className="py-1.5 pr-3">Target</th>
                <th className="py-1.5 pr-3">Profile</th>
                <th className="py-1.5 pr-3">Status</th>
                <th className="py-1.5 pr-3">Created</th>
                <th className="py-1.5 pr-3"></th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.id} className="border-b border-panel-border/60">
                  <td className="py-1.5 pr-3 text-foreground">{s.target}</td>
                  <td className="py-1.5 pr-3 text-foreground-muted">{s.profile}</td>
                  <td className="py-1.5 pr-3 text-accent">{s.status}</td>
                  <td className="py-1.5 pr-3 text-foreground-muted">
                    {new Date(s.created_at).toLocaleString()}
                  </td>
                  <td className="py-1.5 pr-3">
                    <button
                      onClick={() => setCurrentScanId(s.id)}
                      disabled={currentScanId === s.id}
                      className="text-[11px] border border-panel-border rounded px-2 py-0.5 text-foreground-muted hover:text-accent hover:border-accent/40 disabled:opacity-40"
                    >
                      {currentScanId === s.id ? "active" : "select"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  );
}
