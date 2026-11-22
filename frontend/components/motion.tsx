"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { afterFirstInteraction } from "@/lib/first-interaction";
import type { MotionController } from "@/lib/motion/controller";

/**
 * Starts the public site's motion (lib/motion/controller.ts: GSAP scroll animations, Lenis
 * smooth scrolling) in idle time after the visitor's first interaction, so
 * the ~50 KB it loads never weighs on page load. Nothing at all with reduced motion.
 */
export function Motion() {
  const pathname = usePathname();
  const controller = useRef<MotionController | null>(null);

  useEffect(() => {
    const main = document.getElementById("main");
    if (!main || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    let active = true;
    const cancel = afterFirstInteraction(() => {
      import("@/lib/motion/controller")
        .then(({ startMotion }) => {
          if (active) {
            controller.current = startMotion(main);
          }
        })
        // Motion is optional: if its code can't load (offline), the page simply stays still.
        .catch(() => {});
    });
    return () => {
      active = false;
      cancel();
      controller.current?.stop();
      controller.current = null;
    };
  }, []);

  useEffect(() => {
    controller.current?.pageChanged();
  }, [pathname]);

  return null;
}
