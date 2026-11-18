"use client";

import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";

/** A page couldn't load (usually the API is unreachable for a moment). */
export default function SiteError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Container className="flex flex-col items-start gap-8 py-24 sm:py-32">
      <Eyebrow>Something went wrong</Eyebrow>
      <h1 className="font-display text-headline font-extrabold uppercase">
        This page didn&apos;t <span className="text-signal">load.</span>
      </h1>
      <p className="max-w-md text-lg text-muted">
        Part of the site is briefly unavailable. Try again in a moment.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button onClick={reset}>Try again</Button>
        <ButtonLink href="/" variant="outline">
          Back home
        </ButtonLink>
      </div>
    </Container>
  );
}
