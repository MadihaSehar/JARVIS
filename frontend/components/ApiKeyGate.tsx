"use client";

import { useEffect, useState } from "react";
import { api, getApiKey, setApiKey } from "@/lib/api";

type GateState = "checking" | "locked" | "unlocked";

export default function ApiKeyGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<GateState>("checking");
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      let health;
      try {
        health = await api.health();
      } catch {
        // Backend unreachable -- let the app render; StatusBar will show
        // the real "offline" state rather than blocking on a dead gate.
        if (!cancelled) setState("unlocked");
        return;
      }

      if (!health.auth_enabled) {
        if (!cancelled) setState("unlocked");
        return;
      }

      const existing = getApiKey();
      if (!existing) {
        if (!cancelled) setState("locked");
        return;
      }

      try {
        await api.getSettings();
        if (!cancelled) setState("unlocked");
      } catch {
        if (!cancelled) setState("locked");
      }
    }

    check();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setApiKey(input.trim());
    try {
      await api.getSettings();
      setState("unlocked");
    } catch {
      setError("That key was rejected. Check API_KEY in backend/.env.");
    } finally {
      setSubmitting(false);
    }
  }

  if (state === "checking") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-foreground-muted text-[13px] font-mono">Connecting...</p>
      </div>
    );
  }

  if (state === "locked") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm border border-panel-border rounded-lg p-6 bg-panel">
          <h1 className="text-lg font-mono text-accent mb-1">J.A.R.V.I.S.</h1>
          <p className="text-foreground-muted text-[13px] mb-4">
            This instance requires an API key. Find it in <code>backend/.env</code> as{" "}
            <code>API_KEY</code>.
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="password"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="API key"
              autoFocus
              className="w-full bg-background border border-panel-border rounded px-3 py-2 text-[13px] text-foreground font-mono focus:outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={submitting || !input.trim()}
              className="w-full bg-accent-dim text-accent border border-accent/40 rounded px-4 py-2 text-[13px] font-mono hover:bg-accent/20 disabled:opacity-50"
            >
              {submitting ? "Checking..." : "Unlock"}
            </button>
            {error && <div className="text-danger text-[12px] font-mono">{error}</div>}
          </form>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
