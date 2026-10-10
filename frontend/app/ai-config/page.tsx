"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, AiModel, AiStatus } from "@/lib/api";

export default function AiConfigPage() {
  const [status, setStatus] = useState<AiStatus | null>(null);
  const [models, setModels] = useState<AiModel[]>([]);
  const [prompt, setPrompt] = useState("Say hello in exactly five words.");
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setStatus(await api.aiStatus());
      } catch {
        // ignore
      }
      try {
        setModels(await api.aiModels());
      } catch {
        // ignore
      }
    }
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, []);

  async function handleTest(e: React.FormEvent) {
    e.preventDefault();
    setTesting(true);
    setError(null);
    setResult(null);
    setDuration(null);
    try {
      const r = await api.aiTest(prompt);
      if (r.success) {
        setResult(r.response ?? "(empty response)");
        setDuration(r.duration_ms);
      } else {
        setError(r.error ?? "Unknown error from AI provider.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">AI Configuration</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Local inference via Ollama. Cloud providers are disabled by default. The AI layer is
          advisory only -- every AI-proposed action still passes through deterministic policy
          validation, and the system keeps working if the AI is unreachable.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Panel title="Provider Status">
          {status ? (
            <div className="space-y-1 text-[13px] font-mono">
              <div>
                <span className="text-foreground-muted">PROVIDER </span>
                <span className="text-foreground">{status.provider}</span>
              </div>
              <div>
                <span className="text-foreground-muted">INSTALLED </span>
                <span className={status.installed ? "text-success" : "text-danger"}>
                  {String(status.installed)}
                </span>
              </div>
              <div>
                <span className="text-foreground-muted">REACHABLE </span>
                <span className={status.reachable ? "text-success" : "text-danger"}>
                  {String(status.reachable)}
                </span>
              </div>
              {status.base_url && (
                <div>
                  <span className="text-foreground-muted">BASE URL </span>
                  <span className="text-foreground">{status.base_url}</span>
                </div>
              )}
              {status.error && (
                <div>
                  <span className="text-foreground-muted">ERROR </span>
                  <span className="text-danger">{status.error}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-foreground-muted text-[13px]">Loading...</p>
          )}
        </Panel>

        <Panel title={`Available Models (${models.length})`}>
          {models.length === 0 ? (
            <p className="text-foreground-muted text-[13px]">No models found.</p>
          ) : (
            <ul className="space-y-1 text-[13px] font-mono">
              {models.map((m) => (
                <li key={m.name} className="text-foreground">
                  {m.name}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel title="Test Prompt">
        <form onSubmit={handleTest} className="space-y-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            className="w-full bg-background border border-panel-border rounded px-3 py-2 text-[13px] text-foreground font-mono focus:outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={testing}
            className="bg-accent-dim text-accent border border-accent/40 rounded px-4 py-1.5 text-[13px] font-mono hover:bg-accent/20 disabled:opacity-50"
          >
            {testing ? "running..." : "Run Test"}
          </button>
        </form>
        {error && <div className="text-danger text-[12px] mt-3 font-mono">{error}</div>}
        {result && (
          <div className="mt-3 border-t border-panel-border pt-3">
            <div className="text-[11px] text-foreground-muted font-mono mb-1">
              RESPONSE{duration !== null ? ` (${duration}ms)` : ""}
            </div>
            <p className="text-[13px] text-foreground whitespace-pre-wrap">{result}</p>
          </div>
        )}
      </Panel>
    </div>
  );
}
