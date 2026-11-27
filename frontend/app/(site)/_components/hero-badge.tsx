import { getProfile, readAtRequestTimeWithoutApi } from "@/lib/api/public";

/**
 * A still round badge on the hero's block that opens the résumé (the PDF, in a new
 * tab). Only when the profile has a résumé: nothing on the block otherwise.
 */
export async function ResumeBadge() {
  await readAtRequestTimeWithoutApi();
  const resume = (await getProfile())?.resume;
  if (!resume) {
    return null;
  }
  return (
    <a
      href={resume.url}
      target="_blank"
      rel="noopener noreferrer"
      // Inside the block's corner: an ink circle hanging over the edge vanished into the ink page.
      className="group absolute right-4 bottom-4 z-10 flex size-24 flex-col items-center justify-center gap-1 rounded-full bg-ink text-accent transition-transform duration-300 ease-(--ease-ui) hover:scale-105 sm:right-5 sm:bottom-5 sm:size-28"
    >
      <span className="font-display text-xl leading-none sm:text-2xl">Résumé</span>
      {/* ↗ like every résumé link: the PDF opens in a new tab. */}
      <span
        aria-hidden="true"
        className="text-lg leading-none transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
      >
        ↗
      </span>
      <span className="sr-only">(PDF)</span>
    </a>
  );
}
