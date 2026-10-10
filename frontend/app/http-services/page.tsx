"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, Asset } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function HttpServicesPage() {
  const { currentScanId } = useScanContext();
  const [services, setServices] = useState<Asset[]>([]);

  useEffect(() => {
    if (!currentScanId) {
      setServices([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const all = await api.getScanAssets(currentScanId!);
        if (!cancelled) setServices(all.filter((a) => a.asset_type === "http_service"));
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">HTTP Services</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Live HTTP(S) services discovered on resolved hosts, with status code, server header,
          and redirect behavior recorded at probe time.
        </p>
      </div>

      {!currentScanId ? (
        <Panel title="No Active Scan">
          <p className="text-foreground-muted text-[13px]">
            Start a scan from the Reconnaissance page to populate this list.
          </p>
        </Panel>
      ) : services.length === 0 ? (
        <Panel title="HTTP Services">
          <p className="text-foreground-muted text-[13px]">No HTTP services discovered yet.</p>
        </Panel>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {services.map((s) => {
            const meta = (s.meta || {}) as Record<string, unknown>;
            return (
              <Panel key={s.id} title={s.value}>
                <div className="space-y-1 text-[13px] font-mono">
                  <div>
                    <span className="text-foreground-muted">STATUS </span>
                    <span className="text-accent">{String(meta.status_code ?? "-")}</span>
                  </div>
                  <div>
                    <span className="text-foreground-muted">SERVER </span>
                    <span className="text-foreground">{String(meta.server ?? "unknown")}</span>
                  </div>
                  <div>
                    <span className="text-foreground-muted">REDIRECT </span>
                    <span className="text-foreground">{String(meta.redirect ?? "-")}</span>
                  </div>
                  <div>
                    <span className="text-foreground-muted">DISCOVERED </span>
                    <span className="text-foreground">
                      {new Date(s.discovered_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </Panel>
            );
          })}
        </div>
      )}
    </div>
  );
}
