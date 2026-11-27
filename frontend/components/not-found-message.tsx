import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";

/** The 404 message, shared by the site's two not-found pages: the number set as a poster. */
export function NotFoundMessage() {
  return (
    <Container className="flex flex-col items-start gap-8 py-20 sm:py-28">
      <p aria-hidden="true" className="font-display text-[clamp(8rem,30vw,22rem)] leading-[0.8] tracking-[-0.04em] text-accent">
        404
      </p>
      <h1 className="font-display text-headline">Nothing lives at this address.</h1>
      <p className="max-w-md text-lg text-muted">The projects and the contact form are one click away.</p>
      <div className="flex flex-wrap gap-3">
        <ButtonLink href="/projects">See the projects</ButtonLink>
        <ButtonLink href="/" variant="secondary">
          Back home
        </ButtonLink>
      </div>
    </Container>
  );
}
