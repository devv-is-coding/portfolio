"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import type { ColorBendsSettings } from "@/lib/color-bends-webgl";

// The WebGL code loads on the first of these: during page load the shader cost Lighthouse's
// phone profile ~150 ms of blocking time and pushed LCP past 2.5 s, so loading runs without it.
const FIRST_INTERACTION_EVENTS = [
  "pointermove",
  "pointerdown",
  "keydown",
  "scroll",
  "wheel",
  "touchstart",
] as const;

type ColorBendsProps = Partial<ColorBendsSettings> & {
  /** Up to 8 colors: hex (`#f2b43a`) or a theme variable (`--color-accent`). */
  colors: readonly string[];
  className?: string;
};

/**
 * Animated color bands for a background (React Bits' ColorBends, in plain WebGL: see
 * lib/color-bends-webgl.ts). Decorative: hidden from screen readers and the pointer.
 * The WebGL code loads in idle time after the visitor's first interaction, then fades in.
 */
export function ColorBends({
  colors,
  rotation = 90,
  autoRotate = 0,
  speed = 0.2,
  scale = 1,
  frequency = 1,
  warpStrength = 1,
  mouseInfluence = 1,
  parallax = 0.5,
  noise = 0.15,
  iterations = 1,
  intensity = 1.5,
  bandWidth = 6,
  className,
}: ColorBendsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const settingsRef = useRef<ColorBendsSettings | null>(null);
  const colorsRef = useRef<readonly string[]>(colors);

  useEffect(() => {
    settingsRef.current = {
      rotation,
      autoRotate,
      speed,
      scale,
      frequency,
      warpStrength,
      mouseInfluence,
      parallax,
      noise,
      iterations,
      intensity,
      bandWidth,
    };
    colorsRef.current = colors;
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    let stopped = false;
    let stop: (() => void) | null = null;
    let idleId: number | undefined;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    const start = async () => {
      const { startColorBends } = await import("@/lib/color-bends-webgl");
      if (stopped) {
        return;
      }
      stop = startColorBends(canvas, {
        settings: () => settingsRef.current,
        colors: () => colorsRef.current,
      });
      if (stop) {
        canvas.dataset.ready = "";
      }
    };

    // Safari has no requestIdleCallback: a short timeout stands in.
    const scheduleStart = () => {
      if ("requestIdleCallback" in window) {
        idleId = window.requestIdleCallback(() => void start(), { timeout: 2000 });
      } else {
        timeoutId = setTimeout(() => void start(), 300);
      }
    };

    const stopWaiting = () => {
      for (const type of FIRST_INTERACTION_EVENTS) {
        window.removeEventListener(type, onFirstInteraction);
      }
    };
    function onFirstInteraction() {
      stopWaiting();
      scheduleStart();
    }
    for (const type of FIRST_INTERACTION_EVENTS) {
      window.addEventListener(type, onFirstInteraction, { passive: true });
    }

    return () => {
      stopped = true;
      stopWaiting();
      if (idleId !== undefined) {
        window.cancelIdleCallback(idleId);
      }
      clearTimeout(timeoutId);
      stop?.();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={cn(
        "pointer-events-none block size-full opacity-0 transition-opacity duration-1000 data-ready:opacity-100",
        className,
      )}
    />
  );
}
