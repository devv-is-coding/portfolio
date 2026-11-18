import { cn } from "@/lib/cn";

const VARIANTS = {
  primary: "bg-accent text-accent-ink hover:bg-paper",
  outline: "border border-paper/25 text-paper hover:border-accent hover:text-accent",
  ghost: "text-muted hover:bg-paper/5 hover:text-paper",
  danger: "border border-signal/50 text-signal hover:bg-signal hover:text-ink",
} as const;

const SIZES = {
  md: "h-12 px-6 text-base",
  sm: "h-9 px-4 text-sm",
} as const;

export type ButtonVariant = keyof typeof VARIANTS;
export type ButtonSize = keyof typeof SIZES;

export type ButtonStyle = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
};

/** The classes shared by Button and ButtonLink, so links and buttons look the same. */
export function buttonClasses({ variant = "primary", size = "md", className }: ButtonStyle): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors duration-200 disabled:pointer-events-none disabled:opacity-50",
    SIZES[size],
    VARIANTS[variant],
    className,
  );
}
