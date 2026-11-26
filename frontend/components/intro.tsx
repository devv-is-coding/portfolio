"use client";

import { type CSSProperties, useEffect, useRef } from "react";
import { Eyebrow } from "@/components/ui/eyebrow";
import { INTRO_LEAVING, INTRO_PLAYING } from "@/lib/intro";
import { SITE } from "@/lib/site";

// The greeting's words are all in after ~0.8 s (globals.css); then it goes. It never waits for
// the backend: cached pages need neither the API nor its database.
const GREETING_MS = 900;
// The status route gives the API 10 s (lib/api/status.ts); after that the request is dropped.
const WAKE_UP_TIMEOUT_MS = 12_000;
const SKIP_EVENTS = ["pointerdown", "keydown", "wheel", "touchstart"] as const;

// The wake-up request goes out once per page load, even when React runs the effect twice
// (development's Strict Mode does).
let wakeUp: Promise<unknown> | null = null;

const FIRST_NAME = SITE.name.split(" ")[0];
const WORDS = [
  { text: "Hi,", accent: false },
  { text: "I'm", accent: false },
  { text: `${FIRST_NAME}.`, accent: true },
];

/**
 * The welcome screen when a session starts on the home page (lib/intro.ts decides before the
 * first paint). It sends one status request so the API and the free-tier database wake up
 * while the visitor looks around, leaves after the greeting, and at once on a click, key,
 * scroll or touch. Decorative: hidden from screen readers, never in the way.
 */
export function Intro() {
  const overlay = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = document.documentElement;
    const element = overlay.current;
    if (root.dataset.intro !== INTRO_PLAYING || !element) {
      return;
    }
    let active = true;

    const stopSkipping = () => {
      for (const type of SKIP_EVENTS) {
        window.removeEventListener(type, leave);
      }
    };
    function leave() {
      if (active && root.dataset.intro === INTRO_PLAYING) {
        root.dataset.intro = INTRO_LEAVING;
        stopSkipping();
      }
    }

    // One request, whatever it answers: the site never relies on it, it only gives the
    // backend a head start. The body is read so the request closes (an unread one stays open
    // in Chrome).
    wakeUp ??= fetch("/api/status", { cache: "no-store", signal: AbortSignal.timeout(WAKE_UP_TIMEOUT_MS) })
      .then((response) => response.text())
      .catch(() => {});
    const greetingTimer = setTimeout(leave, GREETING_MS);
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
      clearTimeout(greetingTimer);
      stopSkipping();
      element.removeEventListener("animationend", finish);
    };
  }, []);

  return (
    <div ref={overlay} aria-hidden="true" className="intro fixed inset-0 z-60 place-items-center bg-ink px-5">
      <div className="intro-content flex flex-col items-center gap-6 text-center">
        <Eyebrow className="intro-label">Welcome</Eyebrow>
        {/* One line from sm up; on phones the name gets its own line, so it can stay big. */}
        <p className="font-display text-[17vw] leading-[0.9] font-extrabold tracking-[-0.035em] uppercase sm:text-[clamp(3.5rem,13vw,8.5rem)]">
          {WORDS.map((word, index) => (
            <span key={word.text} className={word.accent ? "max-sm:block" : undefined}>
              {index > 0 && " "}
              <span className="motion-word">
                <span
                  className={word.accent ? "motion-word-inner text-accent" : "motion-word-inner"}
                  style={{ "--intro-word": index } as CSSProperties}
                >
                  {word.text}
                </span>
              </span>
            </span>
          ))}
        </p>
      </div>
      <div className="intro-progress absolute inset-x-0 bottom-0 h-px bg-accent" />
    </div>
  );
}
