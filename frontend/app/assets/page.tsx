"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import AssetTable from "@/components/AssetTable";
import { api, Asset } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function AssetsPage() {
  const { currentScanId } = useScanContext();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentScanId) {
      setAssets([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      setLoading(true);
      try {
        const a = await api.getScanAssets(currentScanId!);
        if (!cancelled) setAssets(a);
      } catch {
        // ignore transient errors
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    poll();
    const interval = setInterval(poll, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [currentScanId]);

  const grouped = assets.reduce<Record<string, number>>((acc, a) => {
    acc[a.asset_type] = (acc[a.asset_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Asset Inventory</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          All assets discovered for the active scan, across every type.
        </p>
      </div>

      {!currentScanId && (
        <Panel title="No Active Scan">
          <p className="text-foreground-muted text-[13px]">
            Start a scan from the Reconnaissance page to populate this inventory.
          </p>
        </Panel>
      )}

      {currentScanId && (
        <>
          <Panel title="Summary">
            <div className="flex flex-wrap gap-4 text-[13px] font-mono">
              <div>
                <span className="text-foreground-muted">TOTAL </span>
                <span className="text-foreground">{assets.length}</span>
              </div>
              {Object.entries(grouped).map(([type, count]) => (
                <div key={type}>
                  <span className="text-foreground-muted">{type.toUpperCase()} </span>
                  <span className="text-accent">{count}</span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title={loading ? "All Assets (refreshing...)" : "All Assets"}>
            <AssetTable assets={assets} emptyMessage="No assets discovered yet." />
          </Panel>
        </>
      )}
    </div>
  );
}
