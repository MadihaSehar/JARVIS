"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import AssetTable from "@/components/AssetTable";
import { api, Asset } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function EndpointsPage() {
  const { currentScanId } = useScanContext();
  const [endpoints, setEndpoints] = useState<Asset[]>([]);

  useEffect(() => {
    if (!currentScanId) {
      setEndpoints([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const all = await api.getScanAssets(currentScanId!);
        if (cancelled) return;
        setEndpoints(all.filter((a) => a.asset_type === "endpoint"));
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
        <h1 className="text-xl font-mono text-foreground">Endpoint Discovery</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Application endpoints and routes crawled via Katana, scoped to each discovered HTTP
          service and re-validated against scope before being stored.
        </p>
      </div>

      {!currentScanId ? (
        <Panel title="No Active Scan">
          <p className="text-foreground-muted text-[13px]">
            Start a scan from the Reconnaissance page, then click &quot;Run Discovery&quot; to
            populate this page.
          </p>
        </Panel>
      ) : (
        <Panel title={`Endpoints (${endpoints.length})`}>
          <AssetTable
            assets={endpoints}
            emptyMessage={
              'No endpoints discovered yet. Click "Run Discovery" on the Reconnaissance page ' +
              "(requires at least one discovered HTTP service)."
            }
          />
        </Panel>
      )}
    </div>
  );
}
