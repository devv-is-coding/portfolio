import { ViewTransition } from "react";

/**
 * Page transitions: a template gets a new instance per route, so this view transition
 * enters and exits on every navigation (the CSS for `page-enter` / `page-exit` is in
 * globals.css). The browser animates it natively: no JavaScript beyond React itself.
 */
export default function SiteTemplate({ children }: LayoutProps<"/">) {
  return (
    <ViewTransition enter="page-enter" exit="page-exit" default="none">
      <div>{children}</div>
    </ViewTransition>
  );
}
