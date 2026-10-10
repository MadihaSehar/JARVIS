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
    <div className="border border-panel-border bg-panel rounded-md overflow-hidden">
      <div className="px-4 py-3 border-b border-panel-border flex items-center justify-between">
        <h2 className="text-[13px] font-mono text-foreground-muted tracking-wide uppercase">
          {title}
        </h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
