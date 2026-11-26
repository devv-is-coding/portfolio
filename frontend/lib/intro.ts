/*
 * The welcome screen (components/intro.tsx) plays at most once per browser session, and only
 * when the session starts on the home page. INTRO_GATE_SCRIPT, inline in <head>, decides it
 * before the first paint, so a returning visitor never sees it flash. The decision is
 * `data-intro` on <html>, read by the CSS (globals.css) and by the component.
 */

/** sessionStorage key: set on the session's first public page, so later pages and refreshes skip it. */
export const INTRO_SEEN_KEY = "portfolio:intro-seen";
export const INTRO_PLAYING = "playing";
export const INTRO_LEAVING = "leaving";

// Only when the session starts on the home page: a visitor who arrives on a project or a
// post came for that page and gets it at once, and the visit counts, so the greeting doesn't
// appear later in the session either. Never in the admin, never with reduced motion, and
// nothing when storage is blocked (private modes may throw): then the site simply shows.
export const INTRO_GATE_SCRIPT = `try{var p=location.pathname;if(!p.startsWith("/admin")&&!sessionStorage.getItem("${INTRO_SEEN_KEY}")){sessionStorage.setItem("${INTRO_SEEN_KEY}","1");if(p==="/"&&!matchMedia("(prefers-reduced-motion: reduce)").matches){document.documentElement.dataset.intro="${INTRO_PLAYING}"}}}catch(e){}`;
