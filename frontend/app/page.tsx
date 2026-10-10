"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, AiStatus, AiModel, Scan, ScannerInfo } from "@/lib/api";

export default function OverviewPage() {
  const [health, setHealth] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);
  const [aiModels, setAiModels] = useState<AiModel[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [scanners, setScanners] = useState<ScannerInfo[]>([]);

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("unreachable"));
    api.aiStatus().then(setAiStatus).catch(() => setAiStatus(null));
    api.aiModels().then(setAiModels).catch(() => setAiModels([]));
    api.listScans().then(setScans).catch(() => setScans([]));
    api.listScanners().then(setScanners).catch(() => setScanners([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Overview</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          System health and recent activity.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Panel title="Backend API">
          <div className="text-2xl font-mono text-foreground">
            {health === null ? "..." : health}
          </div>
        </Panel>

        <Panel title="AI Provider (Ollama)">
          {aiStatus ? (
            <div className="space-y-1 text-[13px]">
              <div>
                reachable:{" "}
                <span className={aiStatus.reachable ? "text-success" : "text-danger"}>
                  {String(aiStatus.reachable)}
                </span>
              </div>
              <div className="text-foreground-muted">{aiModels.length} model(s) available</div>
            </div>
          ) : (
            <div className="text-foreground-muted text-[13px]">unknown</div>
          )}
        </Panel>

        <Panel title="Scanner Providers">
          <div className="text-2xl font-mono text-foreground">{scanners.length}</div>
          <div className="text-foreground-muted text-[12px] mt-1">
            {scanners.map((s) => s.name).join(", ") || "none registered"}
          </div>
        </Panel>
      </div>

      <Panel title="Recent Scans">
        {scans.length === 0 ? (
          <div className="text-foreground-muted text-[13px] py-4 text-center">
            No scans yet. Start one from the Reconnaissance panel.
          </div>
        ) : (
          <div className="space-y-2">
            {scans.slice(0, 8).map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between text-[13px] border-b border-panel-border/50 pb-2"
              >
                <span className="font-mono text-foreground">{s.target}</span>
                <span className="text-accent font-mono text-[12px]">{s.status}</span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
