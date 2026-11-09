import type { ReactNode } from "react";

export type WorkspaceIcon = "box" | "notice" | "operation" | "incident" | "settings" | "audit"
  | "pin" | "chevron" | "refresh" | "plus" | "check";

const paths: Record<WorkspaceIcon, string> = {
  box: "m3 7 9-4 9 4-9 4-9-4Zm0 0v10l9 4 9-4V7M12 11v10M7.5 5l9 4",
  notice: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  operation: "M3 8h18M3 16h18M8 4 4 8l4 4m8 0 4 4-4 4",
  incident: "M8 3h6l4 4v14H6V3h2Zm6 0v5h4m-6 3v3m0 3h.01",
  settings: "M4 7h16M4 17h16M9 4v6m6 4v6",
  audit: "M4 4v16h16M8 15v-3m4 3V8m4 7V5",
  pin: "M19 10c0 5-7 10-7 10S5 15 5 10a7 7 0 1 1 14 0Z M12 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
  chevron: "m9 18 6-6-6-6",
  refresh: "M20 10a8 8 0 0 0-14-4L3 9m0 0V4m0 5h5m-4 5a8 8 0 0 0 14 4l3-3m0 0v5m0-5h-5",
  plus: "M12 5v14M5 12h14",
  check: "m5 12 4 4L19 6",
};

export function WorkspaceGlyph({ name, className }: { name: WorkspaceIcon; className?: string }) {
  return <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" focusable="false">
    <path d={paths[name]} />
  </svg>;
}

export function WorkspaceHeading({ id, title, description, action }: {
  id: string; title: string; description?: string; action?: ReactNode;
}) {
  return <div className="workspace-card-heading">
    <div>
      <h2 id={id} tabIndex={-1}>{title}</h2>
      {description && <p>{description}</p>}
    </div>
    {action}
  </div>;
}

export function WorkspaceBadge({ children, tone = "neutral" }: {
  children: ReactNode; tone?: "neutral" | "info" | "good" | "pending";
}) {
  return <span className={"workspace-badge workspace-badge--" + tone}>{children}</span>;
}

export function WorkspaceEmpty({ icon = "box", title, description }: {
  icon?: WorkspaceIcon; title: string; description: string;
}) {
  return <div className="workspace-empty">
    <span className="workspace-empty-icon"><WorkspaceGlyph name={icon} /></span>
    <strong>{title}</strong>
    <p>{description}</p>
  </div>;
}
