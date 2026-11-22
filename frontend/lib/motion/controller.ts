import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { startCoverPreview } from "@/lib/motion/cover-preview";

/*
 * The public site's motion: Lenis smooth scrolling and GSAP scroll animations. Loaded by
 * components/motion.tsx only after the visitor's first interaction (and never with reduced
 * motion), so none of it is in the page's JavaScript budget. The markup works without it:
 * elements opt in with `data-motion`, and nothing is hidden until this code has decided
 * that an element is still below the screen.
 */

gsap.registerPlugin(ScrollTrigger);
// Phones resize the window when the address bar slides away while scrolling; recalculating
// the pinned strip on each of those would make it jump.
ScrollTrigger.config({ ignoreMobileResize: true });

const EASE = "expo.out";
// Frames without scrolling before Lenis stops being ticked (and GSAP's ticker may sleep).
const IDLE_FRAMES_BEFORE_SLEEP = 3;
// The pinned sideways projects strip needs this many cards to have anything to scroll.
const SIDEWAYS_MIN_CARDS = 3;

type Cleanup = () => void;
const NOTHING: Cleanup = () => {};

export type MotionController = {
  /** After a navigation: syncs the smooth scroll with the new position, then `update`s. */
  pageChanged(): void;
  stop(): void;
};

/**
 * Starts smooth scrolling and animates every `[data-motion]` element of the page, looking
 * again whenever `main` (the part that changes between pages) changes.
 */
export function startMotion(main: HTMLElement): MotionController {
  // GSAP's ticker drives Lenis, so ScrollTrigger reads the smoothed position in the same
  // frame, but only while Lenis glides (from a wheel or touch input until it settles): a
  // listener that stays attached keeps the ticker from ever sleeping, so it ran every frame
  // on a page where nothing moved. Lenis gets its own clock, because GSAP's jumps ahead by
  // the time it slept.
  const lenis = new Lenis({ autoRaf: false });
  lenis.on("scroll", ScrollTrigger.update);
  let gliding = false;
  let idleFrames = 0;
  const tick = () => {
    lenis.raf(performance.now());
    // A few still frames in a row, not one: a sleeping ticker runs a new listener at once,
    // before Lenis has started the glide the input asked for.
    idleFrames = lenis.isScrolling ? 0 : idleFrames + 1;
    if (idleFrames > IDLE_FRAMES_BEFORE_SLEEP) {
      gsap.ticker.remove(tick);
      gliding = false;
    }
  };
  lenis.on("virtual-scroll", () => {
    idleFrames = 0;
    if (!gliding) {
      gliding = true;
      // The pause since the last glide isn't one long frame.
      lenis.time = performance.now();
      gsap.ticker.add(tick);
    }
  });

  // Every element seen so far, with what undoes its animation. Next.js keeps visited pages
  // mounted but hidden: their elements are dropped (and shown as they are) while hidden.
  const running = new Map<HTMLElement, Cleanup>();
  const update = () => {
    let changed = false;
    for (const [element, cleanup] of running) {
      if (!isShown(element)) {
        cleanup();
        running.delete(element);
        changed = true;
      }
    }
    for (const element of document.body.querySelectorAll<HTMLElement>("[data-motion]")) {
      if (!running.has(element) && isShown(element)) {
        running.set(element, animate(element));
        changed = true;
      }
    }
    if (changed) {
      ScrollTrigger.refresh();
    }
  };

  // Streamed sections and new pages arrive after the first scan: look again once per frame.
  let frame = 0;
  const scheduleUpdate = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(update);
  };
  const observer = new MutationObserver(scheduleUpdate);
  observer.observe(main, { childList: true, subtree: true });
  update();

  const stopCoverPreview = startCoverPreview();

  return {
    pageChanged() {
      // Next.js has scrolled the new page into place: don't glide on from the old position.
      lenis.scrollTo(window.scrollY, { immediate: true, force: true });
      scheduleUpdate();
    },
    stop() {
      observer.disconnect();
      cancelAnimationFrame(frame);
      for (const cleanup of running.values()) {
        cleanup();
      }
      running.clear();
      stopCoverPreview();
      gsap.ticker.remove(tick);
      gliding = false;
      lenis.destroy();
    },
  };
}

function animate(element: HTMLElement): Cleanup {
  switch (element.dataset.motion) {
    case "words":
      return revealWords(element);
    case "image":
      return revealImage(element);
    case "parallax":
      return parallax(element);
    case "sideways":
      return scrollSideways(element);
    default:
      return NOTHING;
  }
}

/** Laid out on the current page (not inside a hidden one). */
function isShown(element: HTMLElement): boolean {
  return element.isConnected && element.getClientRects().length > 0;
}

/** Still below the screen: animating it can't hide anything the visitor is looking at. */
function isBelowScreen(element: HTMLElement): boolean {
  return element.getBoundingClientRect().top > window.innerHeight;
}

/** A heading's words (components/ui/split-words.tsx) slide up from behind their own edge. */
function revealWords(element: HTMLElement): Cleanup {
  if (!isBelowScreen(element)) {
    return NOTHING;
  }
  const context = gsap.context(() => {
    gsap.from(element.querySelectorAll(".motion-word-inner"), {
      yPercent: 110,
      duration: 1.1,
      ease: EASE,
      stagger: 0.06,
      scrollTrigger: { trigger: element, start: "top 90%", once: true },
    });
  });
  return () => context.revert();
}

/** An image frame uncovers from the bottom while its picture settles from a slight zoom. */
function revealImage(element: HTMLElement): Cleanup {
  if (!isBelowScreen(element)) {
    return NOTHING;
  }
  const picture = element.querySelector("img");
  const context = gsap.context(() => {
    const timeline = gsap.timeline({ scrollTrigger: { trigger: element, start: "top 88%", once: true } });
    // Cleared at the end, so the frame's rounded corners and the hover zoom take over again.
    timeline.fromTo(
      element,
      { clipPath: "inset(100% 0% 0% 0%)" },
      { clipPath: "inset(0% 0% 0% 0%)", duration: 1.3, ease: EASE, clearProps: "clipPath" },
    );
    if (picture) {
      timeline.from(picture, { scale: 1.3, duration: 1.6, ease: EASE, clearProps: "transform" }, 0);
    }
  });
  return () => context.revert();
}

/**
 * Moves `data-motion-y` percent of its height while its section scrolls out (or through),
 * fading to 20% with `data-motion-fade`. It starts from where it is: no jump when it loads.
 */
function parallax(element: HTMLElement): Cleanup {
  const section = element.closest<HTMLElement>("section") ?? element;
  const top = section.getBoundingClientRect().top;
  if (top < 0) {
    return NOTHING;
  }
  const onFirstScreen = top < window.innerHeight;
  const context = gsap.context(() => {
    gsap.to(element, {
      yPercent: Number(element.dataset.motionY ?? "15"),
      opacity: element.hasAttribute("data-motion-fade") ? 0.2 : 1,
      ease: "none",
      scrollTrigger: {
        trigger: section,
        start: onFirstScreen ? "top top" : "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
  });
  return () => context.revert();
}

/**
 * The section pins while its `[data-motion-track]` of cards slides sideways, on every screen
 * (the CSS for `[data-sideways]` lays the cards out in a row, sized per screen). With too few
 * cards the grid stays as it is.
 */
function scrollSideways(section: HTMLElement): Cleanup {
  const track = section.querySelector<HTMLElement>("[data-motion-track]");
  const frame = track?.parentElement;
  // The cards are what changes layout, so they must be out of sight (the section's top
  // padding may already show at the bottom of the screen).
  if (!track || !frame || track.children.length < SIDEWAYS_MIN_CARDS || !isBelowScreen(track)) {
    return NOTHING;
  }
  // How far the row moves: until its last card ends where the content column ends.
  const distance = () => {
    const style = getComputedStyle(frame);
    const content = frame.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    return Math.max(0, track.scrollWidth - content);
  };
  section.dataset.sideways = "";
  const context = gsap.context(() => {
    gsap.to(track, {
      x: () => -distance(),
      ease: "none",
      scrollTrigger: {
        trigger: section,
        // Pinned at the top, or by its bottom edge when it's taller than the screen.
        start: () => (section.offsetHeight > window.innerHeight ? "bottom bottom" : "top top"),
        end: () => `+=${distance()}`,
        pin: true,
        scrub: 1,
        invalidateOnRefresh: true,
      },
    });
  });
  return () => {
    context.revert();
    delete section.dataset.sideways;
  };
}
