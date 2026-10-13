"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import AssetTable from "@/components/AssetTable";
import { api, Asset } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function DirectoriesPage() {
  const { currentScanId } = useScanContext();
  const [directories, setDirectories] = useState<Asset[]>([]);

  useEffect(() => {
    if (!currentScanId) {
      setDirectories([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const all = await api.getScanAssets(currentScanId!);
        if (cancelled) return;
        setDirectories(all.filter((a) => a.asset_type === "directory"));
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
        <h1 className="text-xl font-mono text-foreground">Directory Discovery</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Directory and file brute-forcing against discovered HTTP services, via FFUF with a
          curated default wordlist, conservative thread count, and a hard wall-clock time cap per
          target. Metadata includes response status and redirect destination where applicable.
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
        <Panel title={`Directories/Files (${directories.length})`}>
          <AssetTable
            assets={directories}
            emptyMessage={
              'No directories/files discovered yet. Click "Run Discovery" on the Reconnaissance ' +
              "page (requires at least one discovered HTTP service)."
            }
          />
        </Panel>
      )}
    </div>
  );
}
