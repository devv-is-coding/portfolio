"use client";

import { useEffect } from "react";

/**
 * Scrolls to the section with this id when the URL points at it (`/about#skills`). The
 * browser's own jump misses sections that stream in: it finds the id while React still holds
 * the content in a hidden container and gives up. This runs once the section is on screen.
 */
export function ScrollHere({ id }: { id: string }) {
  useEffect(() => {
    if (window.location.hash === `#${id}`) {
      document.getElementById(id)?.scrollIntoView();
    }
  }, [id]);
  return null;
}
