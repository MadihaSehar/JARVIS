import { Asset } from "@/lib/api";

export default function AssetTable({
  assets,
  emptyMessage,
}: {
  assets: Asset[];
  emptyMessage?: string;
}) {
  if (assets.length === 0) {
    return (
      <div className="text-foreground-muted text-[13px] py-6 text-center">
        {emptyMessage || "No assets discovered yet."}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px] font-mono">
        <thead>
          <tr className="text-left text-foreground-muted border-b border-panel-border">
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Value</th>
            <th className="py-2 pr-4">Metadata</th>
            <th className="py-2">Discovered</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((a) => (
            <tr key={a.id} className="border-b border-panel-border/50 hover:bg-background-elevated/50">
              <td className="py-2 pr-4 text-accent">{a.asset_type}</td>
              <td className="py-2 pr-4 text-foreground">{a.value}</td>
              <td className="py-2 pr-4 text-foreground-muted truncate max-w-xs">
                {Object.keys(a.meta).length > 0 ? JSON.stringify(a.meta) : "-"}
              </td>
              <td className="py-2 text-foreground-muted">
                {new Date(a.discovered_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
