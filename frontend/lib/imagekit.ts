import type { ImageLoaderProps } from "next/image";

/**
 * next/image loader for media-library images: ImageKit resizes and converts on its CDN
 * (`tr=w-…,q-…,f-auto`), so they skip the Next.js optimizer. Other query parameters stay.
 */
export function imagekitLoader({ src, width, quality }: ImageLoaderProps): string {
  const url = new URL(src);
  url.searchParams.set("tr", `w-${width},q-${quality ?? 75},f-auto`);
  return url.toString();
}
