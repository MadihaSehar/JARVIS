import Panel from "@/components/Panel";

export default function EndpointsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Endpoint Discovery</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Application endpoint and route discovery.
        </p>
      </div>

      <Panel title="Not Yet Implemented">
        <p className="text-foreground-muted text-[13px] leading-relaxed">
          Endpoint discovery (crawling and route enumeration, e.g. via a tool such as Katana) is
          not yet integrated into the backend. The current build performs DNS enumeration,
          passive subdomain discovery, HTTP service probing, and safe security-header / reflected-
          input checks. This section will populate once endpoint discovery is added in a later
          phase.
        </p>
      </Panel>
    </div>
  );
}
