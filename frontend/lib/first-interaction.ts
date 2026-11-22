// Signs that a visitor is here and active. Optional heavy code (the WebGL background, GSAP)
// waits for the first one: page load never pays for it, so LCP and blocking time stay low.
const FIRST_INTERACTION_EVENTS = [
  "pointermove",
  "pointerdown",
  "keydown",
  "scroll",
  "wheel",
  "touchstart",
] as const;

/**
 * Calls `callback` once, in idle time after the visitor's first interaction. Browser only.
 * Returns a function that cancels whatever hasn't happened yet.
 */
export function afterFirstInteraction(callback: () => void): () => void {
  let idleId: number | undefined;
  let timeoutId: ReturnType<typeof setTimeout> | undefined;

  const stopWaiting = () => {
    for (const type of FIRST_INTERACTION_EVENTS) {
      window.removeEventListener(type, onFirstInteraction);
    }
  };
  function onFirstInteraction() {
    stopWaiting();
    // Safari has no requestIdleCallback: a short timeout stands in.
    if ("requestIdleCallback" in window) {
      idleId = window.requestIdleCallback(callback, { timeout: 2000 });
    } else {
      timeoutId = setTimeout(callback, 300);
    }
  }
  for (const type of FIRST_INTERACTION_EVENTS) {
    window.addEventListener(type, onFirstInteraction, { passive: true });
  }

  return () => {
    stopWaiting();
    if (idleId !== undefined) {
      window.cancelIdleCallback(idleId);
    }
    clearTimeout(timeoutId);
  };
}
