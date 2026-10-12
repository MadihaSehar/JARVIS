"use client";

import { useEffect, useState } from "react";
import Panel from "@/components/Panel";
import { api, ScannerInfo } from "@/lib/api";

const IMPLEMENTED = [
  { name: "dnspython", purpose: "DNS record enumeration (A/AAAA/MX/NS/TXT/CNAME)" },
  { name: "crt.sh", purpose: "Passive subdomain discovery via certificate transparency" },
  { name: "httpx (Python)", purpose: "HTTP service probing and header retrieval" },
  { name: "security_headers scanner", purpose: "Checks for missing security headers and cookie flags" },
  { name: "reflected_input scanner", purpose: "Canary-based reflected input detection" },
  { name: "open_redirect scanner", purpose: "Canary-based detection of unvalidated redirect parameters" },
  { name: "info_disclosure scanner", purpose: "Probes for exposed .git, .env, and backup files" },
  { name: "cors_misconfig scanner", purpose: "Detects reflected-origin and wildcard+credentials CORS policies" },
];

const NOT_YET_INTEGRATED = [
  "Subfinder", "Amass", "dnsx", "httpx (Go tool)", "Katana", "FFUF", "Nuclei", "OWASP ZAP",
];

export default function ToolIntegrationsPage() {
  const [scanners, setScanners] = useState<ScannerInfo[]>([]);

  useEffect(() => {
    api.listScanners().then(setScanners).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Tool Integrations</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          What this build actually uses today, versus tools named in the original spec that are
          not yet wired in.
        </p>
      </div>

      <Panel title="Registered Scanners">
        {scanners.length === 0 ? (
          <p className="text-foreground-muted text-[13px]">No scanners registered.</p>
        ) : (
          <div className="space-y-1 text-[13px] font-mono">
            {scanners.map((s) => (
              <div key={s.name} className="flex items-center justify-between">
                <span className="text-foreground">{s.name}</span>
                <span className="text-foreground-muted">{s.category}</span>
                <span className="text-accent">{s.risk_level}</span>
                <span className={s.enabled ? "text-success" : "text-foreground-muted"}>
                  {s.enabled ? "enabled" : "disabled"}
                </span>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Implemented Techniques">
        <div className="space-y-2">
          {IMPLEMENTED.map((t) => (
            <div key={t.name} className="text-[13px]">
              <span className="text-foreground font-mono">{t.name}</span>
              <span className="text-foreground-muted"> -- {t.purpose}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Named in Spec, Not Yet Integrated">
        <div className="flex flex-wrap gap-2">
          {NOT_YET_INTEGRATED.map((t) => (
            <span
              key={t}
              className="text-[12px] font-mono border border-panel-border rounded px-2 py-1 text-foreground-muted"
            >
              {t}
            </span>
          ))}
        </div>
        <p className="text-foreground-muted text-[12px] mt-3">
          These external tools are referenced in the original project specification but have not
          been integrated into the backend yet. Current reconnaissance and testing is done with
          the Python-native techniques listed above.
        </p>
      </Panel>
    </div>
  );
}
