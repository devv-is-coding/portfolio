import { gsap } from "gsap";

/*
 * For mouse and trackpad users (never touch screens): a post's cover follows the pointer over
 * a list of posts (`data-motion-preview="<image url>"` on the row). One delegated listener,
 * so new pages and streamed rows need no setup.
 */

const FINE_POINTER = "(hover: hover) and (pointer: fine)";

type Cleanup = () => void;

export function startCoverPreview(): Cleanup {
  if (!window.matchMedia(FINE_POINTER).matches) {
    return () => {};
  }
  // One picture for every row, created here so the server markup stays plain.
  const preview = document.createElement("img");
  preview.alt = "";
  preview.decoding = "async";
  preview.setAttribute("aria-hidden", "true");
  preview.className = "motion-preview";
  document.body.append(preview);
  gsap.set(preview, { xPercent: -50, yPercent: -50, autoAlpha: 0, scale: 0.85 });
  const moveX = gsap.quickTo(preview, "x", { duration: 0.6, ease: "power3.out" });
  const moveY = gsap.quickTo(preview, "y", { duration: 0.6, ease: "power3.out" });
  let current: HTMLElement | null = null;

  const hide = () => {
    current = null;
    gsap.to(preview, { autoAlpha: 0, scale: 0.85, duration: 0.3, ease: "power2.out" });
  };
  const onMove = (event: PointerEvent) => {
    const row = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-motion-preview]") : null;
    if (row !== current) {
      if (!row) {
        hide();
        return;
      }
      if (!current) {
        // Appears where the pointer is, instead of flying in from the last spot.
        gsap.set(preview, { x: event.clientX, y: event.clientY });
      }
      current = row;
      preview.src = row.dataset.motionPreview ?? "";
      gsap.to(preview, { autoAlpha: 1, scale: 1, duration: 0.4, ease: "power3.out" });
    }
    moveX(event.clientX);
    moveY(event.clientY);
  };

  document.addEventListener("pointermove", onMove, { passive: true });
  document.documentElement.addEventListener("pointerleave", hide);
  window.addEventListener("scroll", hide, { passive: true });
  return () => {
    document.removeEventListener("pointermove", onMove);
    document.documentElement.removeEventListener("pointerleave", hide);
    window.removeEventListener("scroll", hide);
    preview.remove();
  };
}
