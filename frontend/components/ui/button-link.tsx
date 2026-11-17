import Link from "next/link";
import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

const VARIANTS = {
  primary: "bg-accent text-accent-ink hover:bg-paper",
  outline: "border border-paper/25 text-paper hover:border-accent hover:text-accent",
} as const;

type ButtonLinkProps = ComponentProps<typeof Link> & {
  variant?: keyof typeof VARIANTS;
};

/** A link styled as a button: the site's calls to action. */
export function ButtonLink({ variant = "primary", className, ...props }: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-base font-semibold transition-colors duration-200",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}
