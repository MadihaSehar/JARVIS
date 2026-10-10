"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import AssetTable from "@/components/AssetTable";
import { api, Asset } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

const DNS_TYPES = new Set(["dns_a", "dns_aaaa", "dns_mx", "dns_ns", "dns_txt", "dns_cname"]);

export default function DnsPage() {
  const { currentScanId } = useScanContext();
  const [records, setRecords] = useState<Asset[]>([]);
  const [subdomains, setSubdomains] = useState<Asset[]>([]);

  useEffect(() => {
    if (!currentScanId) {
      setRecords([]);
      setSubdomains([]);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const all = await api.getScanAssets(currentScanId!);
        if (cancelled) return;
        setRecords(all.filter((a) => DNS_TYPES.has(a.asset_type)));
        setSubdomains(all.filter((a) => a.asset_type === "subdomain"));
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
        <h1 className="text-xl font-mono text-foreground">DNS and Subdomains</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          DNS records resolved directly, and subdomains discovered passively via certificate
          transparency (crt.sh). No direct queries are made against undiscovered hosts.
        </p>
      </div>

      {!currentScanId ? (
        <Panel title="No Active Scan">
          <p className="text-foreground-muted text-[13px]">
            Start a scan from the Reconnaissance page to populate DNS data.
          </p>
        </Panel>
      ) : (
        <>
          <Panel title={`DNS Records (${records.length})`}>
            <AssetTable assets={records} emptyMessage="No DNS records resolved yet." />
          </Panel>
          <Panel title={`Subdomains (${subdomains.length})`}>
            <AssetTable assets={subdomains} emptyMessage="No subdomains discovered yet." />
          </Panel>
        </>
      )}
    </div>
  );
}
