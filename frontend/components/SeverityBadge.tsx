const COLORS: Record<string, string> = {
  critical: "bg-danger/20 text-danger border-danger/40",
  high: "bg-danger/15 text-danger border-danger/30",
  medium: "bg-warning/15 text-warning border-warning/30",
  low: "bg-info/15 text-info border-info/30",
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
