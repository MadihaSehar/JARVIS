import { ReactNode } from "react";

export default function Panel({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="border border-panel-border bg-panel rounded-md overflow-hidden shadow-[0_1px_0_0_rgba(34,211,238,0.12)_inset]">
      <div className="px-4 py-3 border-b border-panel-border flex items-center justify-between">
        <h2 className="text-[12px] font-mono text-foreground-muted tracking-wider uppercase flex items-center gap-2">
          <span className="w-1 h-3 rounded-sm bg-accent/70" />
          {title}
        </h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
