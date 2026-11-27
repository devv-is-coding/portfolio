"use client";

import { useEffect } from "react";

const REVEAL_SELECTOR = "[data-reveal]";

function onScreen(element: Element): boolean {
  const box = element.getBoundingClientRect();
  return box.top < window.innerHeight && box.bottom > 0;
}

/**
 * The site's one motion script (renders nothing): shows `data-reveal` elements as they scroll
 * into view (`data-shown`; globals.css animates). Elements already on screen when it starts are
 * shown at once, so nothing on screen blinks; elements that stream in later are picked up too.
 */
export function MotionObserver() {
  useEffect(() => {
    const reveals = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.setAttribute("data-shown", "");
            reveals.unobserve(entry.target);
          }
        }
      },
      // A little before the element's top reaches the screen's bottom edge.
      { rootMargin: "0px 0px -8% 0px" },
    );

    const watch = (element: Element) => {
      if (element.matches(REVEAL_SELECTOR) && !element.hasAttribute("data-shown")) {
        reveals.observe(element);
      }
    };
    const watchAll = (root: ParentNode) => {
      for (const element of root.querySelectorAll(REVEAL_SELECTOR)) {
        watch(element);
      }
    };

    for (const element of document.querySelectorAll(REVEAL_SELECTOR)) {
      if (onScreen(element)) {
        element.setAttribute("data-shown", "");
      }
    }
    document.documentElement.dataset.motion = "1";
    watchAll(document);

    const additions = new MutationObserver((records) => {
      for (const record of records) {
        for (const node of record.addedNodes) {
          if (node instanceof Element) {
            watch(node);
            watchAll(node);
          }
        }
      }
    });
    additions.observe(document.body, { childList: true, subtree: true });
    return () => {
      additions.disconnect();
      reveals.disconnect();
    };
  }, []);

  return null;
}
