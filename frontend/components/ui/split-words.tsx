import { Fragment } from "react";

/**
 * Text cut into words, each inside its own clipping box, for the slide-up reveal
 * (`data-motion="words"` on the parent, lib/motion/controller.ts). Without the motion code it
 * reads as plain text. The parent should carry the whole text as its `aria-label`, since
 * the pieces are hidden from screen readers.
 */
export function SplitWords({ text }: { text: string }) {
  return text
    .split(/\s+/)
    .filter(Boolean)
    .map((word, index) => (
      <Fragment key={index}>
        {index > 0 && " "}
        <span aria-hidden="true" className="motion-word">
          <span className="motion-word-inner">{word}</span>
        </span>
      </Fragment>
    ));
}
