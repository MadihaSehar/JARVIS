"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import SeverityChart from "@/components/SeverityChart";
import StatTile from "@/components/StatTile";
import { api, AiStatus, AiModel, Asset, Finding, Scan, ScannerInfo, ScanStatus } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

const STATUS_DOT: Record<ScanStatus, string> = {
  running: "bg-accent animate-pulse",
  completed: "bg-success",
  failed: "bg-danger",
  paused: "bg-warning",
  cancelled: "bg-foreground-muted",
  pending: "bg-foreground-muted",
};

function timeAgo(iso: string): string {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function StatusChip({ label, ok }: { label: string; ok: boolean | null }) {
  const dot = ok === null ? "bg-foreground-muted" : ok ? "bg-success" : "bg-danger";
  return (
    <span className="inline-flex items-center gap-2 text-[12px] px-2.5 py-1 rounded-full border border-panel-border bg-background/60">
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

export default function OverviewPage() {
  const { currentScanId, setCurrentScanId } = useScanContext();
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);
  const [aiModels, setAiModels] = useState<AiModel[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [scanners, setScanners] = useState<ScannerInfo[]>([]);
  const [detail, setDetail] = useState<{ scanId: string; assets: Asset[]; findings: Finding[] } | null>(null);

  useEffect(() => {
    api.health().then(() => setBackendUp(true)).catch(() => setBackendUp(false));
    api.aiStatus().then(setAiStatus).catch(() => setAiStatus(null));
    api.aiModels().then(setAiModels).catch(() => setAiModels([]));
    api.listScans().then(setScans).catch(() => setScans([]));
    api.listScanners().then(setScanners).catch(() => setScanners([]));
  }, []);

  // The dashboard summarises the active scan, or the most recent finished
  // one when nothing is selected.
  const focus =
    scans.find((s) => s.id === currentScanId) ??
    scans.find((s) => s.status === "completed") ??
    scans[0] ??
    null;
  const focusId = focus?.id ?? null;

  useEffect(() => {
    if (!focusId) return;
    Promise.all([
      api.getScanAssets(focusId).catch(() => [] as Asset[]),
      api.getScanFindings(focusId).catch(() => [] as Finding[]),
    ]).then(([assets, findings]) => setDetail({ scanId: focusId, assets, findings }));
  }, [focusId]);

  const assets = detail && detail.scanId === focusId ? detail.assets : [];
  const findings = detail && detail.scanId === focusId ? detail.findings : [];

  const urgent = findings.filter((f) => ["critical", "high"].includes(f.severity.toLowerCase())).length;
  const subdomains = assets.filter((a) => a.asset_type === "subdomain").length;
  const services = assets.filter((a) => a.asset_type === "http_service").length;
  const running = scans.filter((s) => s.status === "running").length;

  return (
    <div className="space-y-6">
      <div className="border border-panel-border rounded-md bg-gradient-to-br from-accent/10 via-panel to-panel px-6 py-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono tracking-widest text-accent">J.A.R.V.I.S. // COMMAND CENTER</div>
          <h1 className="text-2xl font-semibold text-foreground mt-1">Security overview</h1>
          <p className="text-foreground-muted text-[13px] mt-1">
            {focus ? (
              <>
                Showing <span className="font-mono text-foreground">{focus.target}</span> &middot;{" "}
                {focus.status} &middot; {timeAgo(focus.created_at)}
              </>
            ) : (
              "No scans yet. Start one from Reconnaissance."
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusChip label="Backend" ok={backendUp} />
          <StatusChip
            label={aiStatus ? `AI · ${aiStatus.provider}${aiModels.length ? ` (${aiModels.length} models)` : ""}` : "AI"}
            ok={aiStatus ? aiStatus.reachable : null}
          />
          <StatusChip label={`${scanners.filter((s) => s.enabled).length} scanners`} ok={scanners.length > 0} />
          <Link
            href="/reconnaissance"
            className="text-[12px] font-mono px-3 py-1 rounded-full bg-accent-dim text-accent border border-accent/40 hover:bg-accent/20"
          >
            + New scan
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile label="Scans" value={scans.length} hint={running ? `${running} running now` : "none running"} />
        <StatTile label="Assets discovered" value={assets.length} hint={`${subdomains} subdomains · ${services} HTTP services`} />
        <StatTile label="Findings" value={findings.length} hint="for the scan shown" />
        <StatTile label="Critical + high" value={urgent} tone={urgent ? "danger" : "default"} hint="need review first" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <Panel
            title="Findings by severity"
            action={
              <Link href="/findings" className="text-[11px] font-mono text-foreground-muted hover:text-accent">
                view all &rarr;
              </Link>
            }
          >
            {findings.length ? (
              <SeverityChart findings={findings} />
            ) : (
              <div className="text-foreground-muted text-[13px] py-6 text-center">No findings for this scan.</div>
            )}
          </Panel>
        </div>
        <div className="lg:col-span-2">
          <Panel title="Scanner providers">
            <div className="space-y-2">
              {scanners.length === 0 && <div className="text-foreground-muted text-[13px]">none registered</div>}
              {scanners.map((s) => (
                <div key={s.name} className="flex items-center justify-between text-[12px]">
                  <span className="font-mono text-foreground">{s.name}</span>
                  <span className="text-foreground-muted">
                    {s.category} &middot; risk {s.risk_level}
                    {!s.enabled && " · off"}
                  </span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>

      <Panel title="Recent scans">
        {scans.length === 0 ? (
          <div className="text-foreground-muted text-[13px] py-4 text-center">
            No scans yet. Start one from the Reconnaissance panel.
          </div>
        ) : (
          <div className="divide-y divide-panel-border/60">
            {scans.slice(0, 8).map((s) => (
              <button
                key={s.id}
                onClick={() => setCurrentScanId(s.id)}
                className={`w-full flex items-center justify-between text-left text-[13px] py-2.5 px-2 rounded hover:bg-background/60 ${
                  s.id === focusId ? "bg-background/60" : ""
                }`}
              >
                <span className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${STATUS_DOT[s.status]}`} />
                  <span className="font-mono text-foreground">{s.target}</span>
                  <span className="text-[11px] text-foreground-muted">{s.profile}</span>
                </span>
                <span className="flex items-center gap-4 text-[12px]">
                  <span className="text-foreground-muted">{timeAgo(s.created_at)}</span>
                  <span className="font-mono text-foreground w-20 text-right">{s.status}</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
