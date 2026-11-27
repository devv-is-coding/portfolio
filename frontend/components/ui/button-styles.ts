import { cn } from "@/lib/cn";

// The poster's pills: a gold primary that steps 14% toward the text colour on hover, an
// outlined secondary that fills with the raised surface. Exactly one filled button marks the
// main action in any view.
const VARIANTS = {
  primary: "bg-accent text-accent-ink hover:bg-[color-mix(in_oklab,var(--color-accent)_86%,var(--color-paper))]",
  secondary: "border border-line text-paper hover:border-paper/40 hover:bg-ink-raised",
  ghost: "text-muted hover:bg-paper/5 hover:text-paper",
  danger: "border border-signal/50 text-signal hover:bg-signal hover:text-ink",
} as const;

const SIZES = {
  md: "h-12 px-6 text-base",
  // 44 px tall on touch screens, so a small button is still a comfortable tap.
  sm: "h-9 px-4 text-sm pointer-coarse:h-11",
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
    // Hover steps the box up 1px and a press sinks it 1px and scales .985, on a fine pointer
    // only (the skill's motion layer: 150ms in, 90ms press).
    "inline-flex items-center justify-center gap-2 rounded-btn font-semibold whitespace-nowrap transition-[background-color,color,border-color,translate,scale] duration-150 ease-(--ease-ui) pointer-fine:hover:-translate-y-px pointer-fine:active:translate-y-px pointer-fine:active:scale-[.985] active:duration-[90ms] disabled:pointer-events-none disabled:opacity-50",
    SIZES[size],
    VARIANTS[variant],
    className,
  );
}
