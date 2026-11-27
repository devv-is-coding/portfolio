"use client";

import { OutageMessage } from "@/components/outage-message";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";

/** A page couldn't load; the message says when the database or the server is offline. */
export default function SiteError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Container className="flex flex-col items-start gap-8 py-20 sm:py-28">
      <p aria-hidden="true" className="font-display text-[clamp(5rem,16vw,13rem)] leading-[0.82] tracking-[-0.04em] text-accent">
        Didn&apos;t load
      </p>
      <h1 className="font-display text-headline">This page couldn&apos;t load.</h1>
      <OutageMessage
        fallback="Part of the site is briefly unavailable. Try again in a moment."
        className="max-w-md text-lg text-muted"
      />
      <div className="flex flex-wrap gap-3">
        <Button onClick={reset}>Try again</Button>
        <ButtonLink href="/" variant="secondary">
          Back home
        </ButtonLink>
      </div>
    </Container>
  );
}
