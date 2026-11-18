import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

/** The small mono label above a headline. */
export function Eyebrow({ className, children, ...props }: ComponentProps<"p">) {
  return (
    <p
      className={cn(
        "flex items-center gap-3 font-mono text-xs uppercase tracking-[0.2em] text-muted",
        className,
      )}
      {...props}
    >
      <span aria-hidden="true" className="size-2 rounded-full bg-accent" />
      {children}
    </p>
  );
}
