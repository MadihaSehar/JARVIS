export default function StatTile({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: number | string;
  hint?: string;
  tone?: "default" | "danger";
}) {
  return (
    <div className="border border-panel-border bg-panel rounded-md px-4 py-4">
      <div className="text-[12px] text-foreground-muted">{label}</div>
      <div
        className={`mt-1 text-3xl font-semibold tabular-nums ${
          tone === "danger" ? "text-sev-critical" : "text-foreground"
        }`}
      >
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {hint && <div className="mt-1 text-[11px] text-foreground-muted truncate">{hint}</div>}
    </div>
  );
}
