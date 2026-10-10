"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, AppSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSettings()
      .then(setSettings)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Settings</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Read-only view of the backend's non-secret configuration. API keys and credentials are
          never exposed here or by the backend's settings endpoint.
        </p>
      </div>

      {error && (
        <Panel title="Error">
          <p className="text-danger text-[13px] font-mono">{error}</p>
        </Panel>
      )}

      {settings && (
        <Panel title="Configuration">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[13px] font-mono">
            {Object.entries(settings).map(([key, value]) => (
              <div key={key}>
                <div className="text-foreground-muted text-[11px]">{key.toUpperCase()}</div>
                <div className="text-foreground">{String(value)}</div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
