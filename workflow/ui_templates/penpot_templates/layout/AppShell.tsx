import type { PropsWithChildren } from "react";
import "../theme.css";

export type AppShellProps = PropsWithChildren<{
  title: string;
  subtitle: string;
}>;

export function AppShell({ title, subtitle, children }: AppShellProps) {
  return (
    <div className="gr-shell-bg">
      <header className="gr-shell-header">
        <div>
          <p className="gr-kicker">GrassRoots One-Pager</p>
          <h1>{title}</h1>
          <p className="gr-subtitle">{subtitle}</p>
        </div>
      </header>
      <main className="gr-shell-content">{children}</main>
    </div>
  );
}
