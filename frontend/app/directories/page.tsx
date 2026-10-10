import Panel from "@/components/Panel";

export default function DirectoriesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-mono text-foreground">Directory Discovery</h1>
        <p className="text-foreground-muted text-[13px] mt-1">
          Directory and file brute-forcing against discovered HTTP services.
        </p>
      </div>

      <Panel title="Not Yet Implemented">
        <p className="text-foreground-muted text-[13px] leading-relaxed">
          Directory/file brute-forcing (e.g. via a tool such as FFUF) is not yet integrated into
          the backend. Adding it will require careful rate limiting and scope enforcement since,
          unlike the current passive and safe-active checks, brute-forcing generates a high volume
          of requests against the target. This section will populate once that work is complete.
        </p>
      </Panel>
    </div>
  );
}
