/*
 * The welcome screen (components/intro.tsx) plays once per browser session. Whether it plays
 * is decided by INTRO_GATE_SCRIPT, inline in <head>, before the first paint: a returning
 * visitor never sees it flash. The decision is `data-intro` on <html>, read by the CSS
 * (globals.css) and by the component.
 */

/** sessionStorage key: set once the intro has started, so refreshes and new pages skip it. */
export const INTRO_SEEN_KEY = "portfolio:intro-seen";
export const INTRO_PLAYING = "playing";
export const INTRO_LEAVING = "leaving";

// Never in the admin, never with reduced motion, and nothing when storage is blocked
// (private modes may throw): then the site simply shows at once.
export const INTRO_GATE_SCRIPT = `try{if(!location.pathname.startsWith("/admin")&&!sessionStorage.getItem("${INTRO_SEEN_KEY}")&&!matchMedia("(prefers-reduced-motion: reduce)").matches){sessionStorage.setItem("${INTRO_SEEN_KEY}","1");document.documentElement.dataset.intro="${INTRO_PLAYING}"}}catch(e){}`;
