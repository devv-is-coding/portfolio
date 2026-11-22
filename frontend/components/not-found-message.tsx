import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";

/** The 404 message, shared by the site's two not-found pages. */
export function NotFoundMessage() {
  return (
    <Container className="flex flex-col items-start gap-8 py-24 sm:py-32">
      <Eyebrow>Error 404</Eyebrow>
      <h1 className="font-display text-headline font-extrabold uppercase">
        Nothing <span className="text-accent">here.</span>
      </h1>
      <p className="max-w-md text-lg text-muted">This page doesn&apos;t exist, or not yet. The home page does.</p>
      <ButtonLink href="/">Back home</ButtonLink>
    </Container>
  );
}
