const COLORS: Record<string, string> = {
  critical: "bg-sev-critical/20 text-sev-critical border-sev-critical/40",
  high: "bg-sev-high/15 text-sev-high border-sev-high/30",
  medium: "bg-sev-medium/15 text-sev-medium border-sev-medium/30",
  low: "bg-sev-low/15 text-sev-low border-sev-low/30",
  info: "bg-panel-border text-foreground-muted border-panel-border",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  const cls = COLORS[severity.toLowerCase()] || COLORS.info;
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono uppercase ${cls}`}>
      {severity}
    </span>
  );
}
