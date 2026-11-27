"use client";

import { useEffect, useRef } from "react";
import { INTRO_LEAVING, INTRO_PLAYING, INTRO_WAKE } from "@/lib/intro";
import { SITE } from "@/lib/site";

// On screen at least 2.5 s (user, 2026-11-26), counted from the first paint: long enough to give
// the API and the free database a head start on a cold start, then the site shows whether or not
// the server has answered (cached pages need neither). The counter reaches 100 in the same time.
const GREETING_MS = 2500;
// The hero's cream block (components hero.tsx): the screen shrinks into it as it leaves.
const TARGET_SELECTOR = "[data-intro-target]";
// The counter's digit strips (globals.css slides them): hundreds 0-1, tens and ones 0-9 then 0.
// One text line per digit in a single element each (white-space: pre): 3 elements to lay out
// at the counter's huge size instead of 33.
const TEN_DIGITS = "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n0";
const DIGIT_STRIPS = ["0\n1", TEN_DIGITS, TEN_DIGITS] as const;
// A browser without paint timing starts the count this long after the script.
const NO_PAINT_ENTRY_MS = 300;
// The status route gives the API 10 s (lib/api/status.ts); after that the request is dropped.
const WAKE_UP_TIMEOUT_MS = 12_000;
const SKIP_EVENTS = ["pointerdown", "keydown", "wheel", "touchstart"] as const;

// The wake-up request goes out once per page load, even when React runs the effect twice
// (development's Strict Mode does).
let wakeUp: Promise<unknown> | null = null;

/**
 * Calls `callback` `ms` after the page's first paint (the script can run before it, which made
 * the greeting's time on screen short of 2.5 s). Returns a cancel function.
 */
function afterFirstPaint(ms: number, callback: () => void): () => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let started = false;
  const start = (paintedAt: number) => {
    if (!started) {
      started = true;
      timer = setTimeout(callback, Math.max(0, paintedAt + ms - performance.now()));
    }
  };
  const painted = performance.getEntriesByName("first-contentful-paint")[0];
  if (painted) {
    start(painted.startTime);
    return () => clearTimeout(timer);
  }
  // A browser without paint timing starts the count a moment after the script instead.
  if (!PerformanceObserver.supportedEntryTypes?.includes("paint")) {
    const fallback = setTimeout(() => start(performance.now()), NO_PAINT_ENTRY_MS);
    return () => {
      clearTimeout(fallback);
      clearTimeout(timer);
    };
  }
  const observer = new PerformanceObserver((list) => {
    const entry = list.getEntriesByName("first-contentful-paint")[0];
    if (entry) {
      observer.disconnect();
      start(entry.startTime);
    }
  });
  observer.observe({ type: "paint", buffered: true });
  return () => {
    observer.disconnect();
    clearTimeout(timer);
  };
}

/**
 * Points the exit at the hero's block: `--intro-to` is the transform that moves and scales the
 * full-screen panel onto the block's box (globals.css animates it: transform and opacity only,
 * so the compositor does the work). Without the block (or off screen) the CSS default lifts
 * the screen away instead.
 */
function aimAtTarget(element: HTMLElement) {
  const target = document.querySelector(TARGET_SELECTOR)?.getBoundingClientRect();
  if (!target || target.bottom <= 0 || target.top >= window.innerHeight) {
    return;
  }
  const scaleX = target.width / window.innerWidth;
  const scaleY = target.height / window.innerHeight;
  element.style.setProperty(
    "--intro-to",
    `translate(${Math.round(target.left)}px, ${Math.round(target.top)}px) scale(${scaleX.toFixed(4)}, ${scaleY.toFixed(4)})`,
  );
}

/** One status request, whatever it answers: the site never relies on it, it only gives the
 * backend a head start. The body is read so the request closes (an unread one stays open in
 * Chrome). */
function wakeUpBackend() {
  wakeUp ??= fetch("/api/status", { cache: "no-store", signal: AbortSignal.timeout(WAKE_UP_TIMEOUT_MS) })
    .then((response) => response.text())
    .catch(() => {});
}

/**
 * The welcome screen when a session starts on the home page (lib/intro.ts decides before the
 * first paint), and the wake-up request on a session's first page, whichever it is. The
 * greeting counts to 100 and leaves after 2.5 s (at once on a click, key, scroll or touch),
 * shrinking into the hero's cream block. Decorative:
 * hidden from screen readers, never in the way.
 */
export function Intro() {
  const overlay = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = document.documentElement;
    if (root.dataset[INTRO_WAKE]) {
      wakeUpBackend();
    }
    const current = overlay.current;
    if (root.dataset.intro !== INTRO_PLAYING || !current) {
      return;
    }
    // Narrowed once here: the hoisted leave() below can't see the check above.
    const element: HTMLDivElement = current;
    let active = true;

    const stopSkipping = () => {
      for (const type of SKIP_EVENTS) {
        window.removeEventListener(type, leave);
      }
    };
    function leave() {
      if (active && root.dataset.intro === INTRO_PLAYING) {
        aimAtTarget(element);
        root.dataset.intro = INTRO_LEAVING;
        stopSkipping();
      }
    }

    // The script times the exit from here on: the CSS fallback for pages without JavaScript
    // (globals.css) stands down, so a late first paint still gets its full 2.5 s.
    root.dataset.introTimed = "1";
    const cancelGreeting = afterFirstPaint(GREETING_MS, leave);
    for (const type of SKIP_EVENTS) {
      window.addEventListener(type, leave, { passive: true });
    }

    // Gone once its exit has played: the attribute (and with it the overlay) goes away.
    const finish = (event: AnimationEvent) => {
      if (event.target === element && event.animationName === "intro-out") {
        delete root.dataset.intro;
      }
    };
    element.addEventListener("animationend", finish);

    return () => {
      active = false;
      cancelGreeting();
      stopSkipping();
      element.removeEventListener("animationend", finish);
    };
  }, []);

  return (
    <div
      ref={overlay}
      aria-hidden="true"
      className="intro fixed inset-0 z-60 grid-rows-[auto_1fr_auto] bg-accent px-5 py-6 text-accent-ink sm:px-8 sm:py-8"
    >
      {/* In the headline cut (bold, narrow) like the counter, so the whole screen reads as one poster. */}
      {/* Phones: one under the other, so neither wraps. */}
      <div className="intro-content flex flex-col gap-2 font-display text-[clamp(1.5rem,2.6vw,2.5rem)] leading-none tracking-[-0.02em] sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <span className="motion-word">
          <span className="motion-word-inner">{SITE.name}</span>
        </span>
        <span className="motion-word sm:text-right">
          <span className="motion-word-inner [animation-delay:90ms]">Full-stack developer · Portfolio</span>
        </span>
      </div>
      {/* The counter: digit strips painted once and slid by CSS (globals.css), never rewritten
          by a script, so no new text paints as it counts (it would become the page's largest
          paint near the end and push LCP past 2.5 s). */}
      <p className="intro-content intro-count flex items-start self-end font-display text-[clamp(7rem,30vw,22rem)] leading-none tracking-[-0.04em] tabular-nums">
        {DIGIT_STRIPS.map((strip, column) => (
          <span key={column} className="intro-digit">
            <span className="intro-strip">{strip}</span>
          </span>
        ))}
        <span className="ml-[0.06em] text-[0.2em] leading-[1.6]">%</span>
      </p>
      <div className="intro-content intro-track mt-5 h-[3px]">
        <div className="intro-progress h-full bg-accent-ink" />
      </div>
    </div>
  );
}
