type MarqueeProps = {
  items: readonly string[];
};

// Each half repeats the words until it is wider than any screen (5 x ~830 px at sm:text-3xl),
// so the strip never shows a gap. --animate-marquee's duration is tuned to this length.
const REPEATS = 5;

/**
 * A decorative strip of words scrolling sideways forever, in CSS only (no JavaScript).
 * It holds two identical halves and moves by half its width, so the loop is seamless.
 * Hidden from screen readers: it repeats text, it doesn't add any.
 */
export function Marquee({ items }: MarqueeProps) {
  const half = Array.from({ length: REPEATS }, () => items).flat();

  return (
    // Positioned above the hero's portrait, which sinks behind it on scroll (lib/motion parallax).
    <div aria-hidden="true" className="relative z-10 overflow-hidden border-y border-line bg-ink-raised text-paper">
      <div className="flex w-max animate-marquee">
        {[0, 1].map((copy) => (
          <ul
            key={copy}
            className="flex shrink-0 items-center gap-8 py-4 pr-8 font-display text-2xl font-extrabold uppercase sm:text-3xl"
          >
            {half.map((item, index) => (
              <li key={index} className="flex items-center gap-8">
                {item}
                <span className="text-xl text-accent">✦</span>
              </li>
            ))}
          </ul>
        ))}
      </div>
    </div>
  );
}
