"use client";

import { Component, type ReactNode } from "react";
import { Container } from "@/components/ui/container";

type Props = { children: ReactNode };
type State = { failed: boolean };

/**
 * An error boundary for optional parts of a page (the home sections below the hero): when the
 * API fails there, the rest of the page still shows. A plain React boundary instead of
 * next/error's catchError (about 10 KB more on every page): these sections never redirect
 * or call notFound(), the cases catchError adds.
 */
export class SectionErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) {
      return this.props.children;
    }
    return (
      <Container className="flex flex-col items-start gap-4 border-t border-line py-16">
        <p className="text-muted">This part of the page couldn&apos;t load right now.</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="rounded-full border border-paper/25 px-4 py-2 text-sm font-semibold hover:border-accent hover:text-accent"
        >
          Try again
        </button>
      </Container>
    );
  }
}
