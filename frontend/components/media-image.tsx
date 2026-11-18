import { getImageProps, type ImageLoaderProps } from "next/image";

/** ImageKit resizes and converts on its CDN (`tr=w-…,q-…,f-auto`): no Next.js optimizer needed. */
function imagekitLoader({ src, width, quality }: ImageLoaderProps): string {
  const url = new URL(src);
  url.searchParams.set("tr", `w-${width},q-${quality ?? 75},f-auto`);
  return url.toString();
}

type MediaImageProps = {
  src: string;
  alt: string;
  /** The image's real size from the API, so the browser reserves its space (no layout shift). */
  width: number | null;
  height: number | null;
  sizes: string;
  loading?: "eager" | "lazy";
  fetchPriority?: "high" | "low" | "auto";
  className?: string;
};

/**
 * An image from the media library (ImageKit), sized for the space it takes. Rendered on the
 * server from getImageProps(): the same responsive srcset as next/image, but no browser
 * JavaScript. The <picture> wrapper has `display: contents`, so it doesn't affect layout.
 */
export function MediaImage({ src, alt, width, height, sizes, loading, fetchPriority, className }: MediaImageProps) {
  const { props } = getImageProps({
    loader: imagekitLoader,
    src,
    alt,
    width: width ?? 1600,
    height: height ?? 900,
    sizes,
    loading,
    fetchPriority,
  });
  return (
    <picture className="contents">
      <img {...props} alt={alt} className={className} />
    </picture>
  );
}
