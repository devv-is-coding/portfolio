import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";

export const metadata: Metadata = {
  title: "Page not found",
};

export default function NotFound() {
  return (
    <Container className="flex flex-col items-start gap-8 py-24 sm:py-32">
      <Eyebrow>Error 404</Eyebrow>
      <h1 className="font-display text-display font-extrabold uppercase">
        Nothing <span className="text-signal">here.</span>
      </h1>
      <p className="max-w-md text-lg text-muted">
        This page doesn&apos;t exist, or not yet. The home page does.
      </p>
      <ButtonLink href="/">Back home</ButtonLink>
    </Container>
  );
}
