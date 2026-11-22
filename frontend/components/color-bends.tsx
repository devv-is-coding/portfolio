"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";
import type { ColorBendsSettings } from "@/lib/color-bends-webgl";
import { afterFirstInteraction } from "@/lib/first-interaction";

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

    // During page load the shader cost Lighthouse's phone profile ~150 ms of blocking time and
    // pushed LCP past 2.5 s, so it waits for the visitor's first interaction.
    const cancel = afterFirstInteraction(() => void start());

    return () => {
      stopped = true;
      cancel();
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
