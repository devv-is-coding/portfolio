import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const TONES = {
  error: "border-signal/50 bg-signal/10 text-paper",
  success: "border-accent/50 bg-accent/10 text-paper",
} as const;

type AlertProps = {
  tone?: keyof typeof TONES;
  children: ReactNode;
  className?: string;
};

/** A message above a form or list. Errors are announced at once (role="alert"). */
export function Alert({ tone = "error", children, className }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn("rounded-xl border px-4 py-3 text-sm", TONES[tone], className)}
    >
      {children}
    </div>
  );
}
