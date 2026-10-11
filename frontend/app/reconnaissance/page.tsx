"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import LiveEventFeed from "@/components/LiveEventFeed";
import AssetTable from "@/components/AssetTable";
import { api, ActionProposal, Asset, Scan, ScanProfile } from "@/lib/api";
import { useScanContext } from "@/lib/scan-context";

export default function ReconnaissancePage() {
  const { currentScanId, setCurrentScanId } = useScanContext();
  const [target, setTarget] = useState("");
  const [profile, setProfile] = useState<ScanProfile>("standard");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [proposals, setProposals] = useState<ActionProposal[]>([]);

  useEffect(() => {
    if (!currentScanId) {
      setScan(null);
      return;
    }
    let cancelled = false;
    async function poll() {
      try {
        const s = await api.getScan(currentScanId!);
        if (!cancelled) setScan(s);
        const a = await api.getScanAssets(currentScanId!);
        if (!cancelled) setAssets(a);
        const p = await api.getProposals(currentScanId!);
        if (!cancelled) setProposals(p);
      } catch {
        // ignore transient errors
      }
    }
    poll();
    const interval = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [currentScanId]);

  async function handleCreateAndStart(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const created = await api.createScan(target.trim(), profile);
      setCurrentScanId(created.id);
      await api.startScan(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  async function handleOrchestrate() {
    if (!currentScanId) return;
    setActionMsg("Starting AI orchestration...");
    try {
      await api.orchestrate(currentScanId);
      setActionMsg("Orchestration started -- see events below and the Findings/AI panels.");
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleSecurityScan() {
    if (!currentScanId) return;
    setActionMsg("Starting security scan...");
    try {
      await api.triggerSecurityScan(currentScanId);
      setActionMsg("Security scan started -- check Findings for results.");
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Reconnaissance</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Enter an authorized target to begin scope-validated reconnaissance.
        </p>
      </div>

      <Panel title="New Scan">
        <form onSubmit={handleCreateAndStart} className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[11px] text-foreground-muted font-mono">TARGET</label>
            <input
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="example.com"
              required
              className="bg-background border border-panel-border rounded px-3 py-1.5 text-[13px] text-foreground font-mono w-64 focus:outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] text-foreground-muted font-mono">PROFILE</label>
            <select
              value={profile}
              onChange={(e) => setProfile(e.target.value as ScanProfile)}
              className="bg-background border border-panel-border rounded px-3 py-1.5 text-[13px] text-foreground font-mono focus:outline-none focus:border-accent"
            >
              <option value="passive">passive</option>
              <option value="standard">standard</option>
              <option value="deep">deep</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={creating}
            className="bg-accent-dim text-accent border border-accent/40 rounded px-4 py-1.5 text-[13px] font-mono hover:bg-accent/20 disabled:opacity-50"
          >
            {creating ? "starting..." : "Create & Start"}
          </button>
        </form>
        {error && <div className="text-danger text-[12px] mt-2 font-mono">{error}</div>}
      </Panel>

      {currentScanId && (
        <>
          <Panel
            title="Active Scan"
            action={
              <div className="flex gap-2">
                <button
                  onClick={handleOrchestrate}
                  className="text-[11px] font-mono border border-panel-border rounded px-2 py-1 text-foreground-muted hover:text-accent hover:border-accent/40"
                >
                  Run AI Orchestration
                </button>
                <button
                  onClick={handleSecurityScan}
                  className="text-[11px] font-mono border border-panel-border rounded px-2 py-1 text-foreground-muted hover:text-accent hover:border-accent/40"
                >
                  Run Security Scan
                </button>
              </div>
            }
          >
            {scan && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[13px] font-mono">
                <div>
                  <div className="text-foreground-muted text-[11px]">TARGET</div>
                  <div className="text-foreground">{scan.target}</div>
                </div>
                <div>
                  <div className="text-foreground-muted text-[11px]">STATUS</div>
                  <div className="text-accent">{scan.status}</div>
                </div>
                <div>
                  <div className="text-foreground-muted text-[11px]">PROFILE</div>
                  <div className="text-foreground">{scan.profile}</div>
                </div>
                <div>
                  <div className="text-foreground-muted text-[11px]">ASSETS</div>
                  <div className="text-foreground">{assets.length}</div>
                </div>
              </div>
            )}
            {actionMsg && <div className="text-foreground-muted text-[12px] mt-3">{actionMsg}</div>}
          </Panel>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Panel title="Live Events">
              <LiveEventFeed scanId={currentScanId} />
            </Panel>
            <Panel title="Discovered Assets">
              <div className="max-h-80 overflow-y-auto">
                <AssetTable assets={assets} />
              </div>
            </Panel>
          </div>

          <Panel title={`AI Action Proposals (${proposals.length})`}>
            {proposals.length === 0 ? (
              <p className="text-foreground-muted text-[13px]">
                No proposals yet. Click "Run AI Orchestration" above to generate some -- the AI
                (or the deterministic fallback, if the AI is unreachable) will suggest which
                assets deserve priority review, and every proposal shown here already passed or
                failed the policy gate independently of what the AI claimed.
              </p>
            ) : (
              <div className="space-y-2">
                {proposals.map((p) => (
                  <div key={p.id} className="border border-panel-border rounded p-3 text-[13px]">
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-foreground">{p.action_type}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-foreground-muted text-[11px]">
                          source: {p.source}
                        </span>
                        <span
                          className={
                            p.status === "approved"
                              ? "text-success"
                              : p.status === "rejected"
                                ? "text-danger"
                                : "text-warning"
                          }
                        >
                          {p.status}
                        </span>
                      </div>
                    </div>
                    <p className="text-foreground-muted mt-1">{p.rationale}</p>
                    <div className="flex items-center gap-3 mt-2 text-[11px] font-mono text-foreground-muted">
                      <span>confidence: {p.confidence}</span>
                      {p.policy_reason && <span>policy: {p.policy_reason}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}
