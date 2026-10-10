"use client";

import { useEffect, useState } from "react";
import { api, AiStatus, Scan } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

function Pill({ label, tone }: { label: string; tone: "ok" | "warn" | "bad" | "neutral" }) {
  const colors: Record<string, string> = {
    ok: "bg-success/15 text-success border-success/30",
    warn: "bg-warning/15 text-warning border-warning/30",
    bad: "bg-danger/15 text-danger border-danger/30",
    neutral: "bg-panel text-foreground-muted border-panel-border",
  };
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded border font-mono ${colors[tone]}`}>
      {label}
    </span>
  );
}

export default function StatusBar() {
  const { currentScanId } = useScanContext();
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        await api.health();
        if (!cancelled) setBackendUp(true);
      } catch {
        if (!cancelled) setBackendUp(false);
      }
      try {
        const status = await api.aiStatus();
        if (!cancelled) setAiStatus(status);
      } catch {
        if (!cancelled) setAiStatus(null);
      }
    }

    poll();
    const interval = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (!currentScanId) {
      setScan(null);
      return;
    }
    async function load() {
      try {
        const s = await api.getScan(currentScanId!);
        if (!cancelled) setScan(s);
      } catch {
        if (!cancelled) setScan(null);
      }
    }
    load();
    const interval = setInterval(load, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [currentScanId]);

  return (
    <div className="h-12 shrink-0 border-b border-panel-border bg-background-elevated px-5 flex items-center justify-between font-mono">
      <div className="flex items-center gap-3">
        <Pill label={backendUp === null ? "CONNECTING" : backendUp ? "BACKEND ONLINE" : "BACKEND DOWN"} tone={backendUp ? "ok" : backendUp === false ? "bad" : "neutral"} />
        {scan ? (
          <span className="text-[12px] text-foreground-muted">
            target: <span className="text-foreground">{scan.target}</span> &middot; status:{" "}
            <span className="text-accent">{scan.status}</span>
          </span>
        ) : (
          <span className="text-[12px] text-foreground-muted">no active scan</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {aiStatus ? (
          <Pill
            label={`AI: ${aiStatus.provider} ${aiStatus.reachable ? "REACHABLE" : "UNREACHABLE"}`}
            tone={aiStatus.reachable ? "ok" : "bad"}
          />
        ) : (
          <Pill label="AI: UNKNOWN" tone="neutral" />
        )}
      </div>
    </div>
  );
}
