import Panel from "@/components/Panel";

export default function ThreatIntelPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Threat Intelligence</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          External threat intelligence enrichment for discovered assets.
        </p>
      </div>

      <Panel title="Not Yet Implemented">
        <p className="text-foreground-muted text-[13px] leading-relaxed">
          Threat intelligence enrichment (CVE correlation, reputation lookups, breach data, etc.)
          is not yet integrated into the backend. The current build focuses on authorized
          reconnaissance and safe, evidence-based security testing. This section will populate
          once a threat intelligence source is wired in during a later phase.
        </p>
      </Panel>
    </div>
  );
}
