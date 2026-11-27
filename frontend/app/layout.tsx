import type { Metadata, Viewport } from "next";
import { Instrument_Sans } from "next/font/google";
import { Intro } from "@/components/intro";
import { INTRO_GATE_SCRIPT } from "@/lib/intro";
import { SITE } from "@/lib/site";
import "./globals.css";

// One family for the whole site (TODO.md Redesign, the poster): Instrument Sans as one variable
// file with its width axis, so text runs at normal width and headlines at 700 narrowed to 75%
// (the `font-display` utility in globals.css) without a second font.
const instrumentSans = Instrument_Sans({
  variable: "--font-instrument-sans",
  subsets: ["latin"],
  axes: ["wdth"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.title, template: `%s · ${SITE.name}` },
  description: SITE.description,
  applicationName: SITE.name,
  authors: [{ name: SITE.name, url: SITE.url }],
  openGraph: { type: "website", siteName: SITE.name, locale: "en_US" },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = {
  themeColor: "#12110f",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // suppressHydrationWarning: the gate script in <body> may add data-intro to <html> before
    // React hydrates; it applies to <html>'s own attributes only, not to anything inside it.
    <html
      lang="en"
      className={`${instrumentSans.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col bg-ink font-sans text-paper">
        {/* Decides, before anything below it is painted, whether the welcome screen plays
            (lib/intro.ts): inline and tiny, so a returning visitor never sees it flash. First in
            <body>, not in <head>: browser extensions add their own scripts to <head>, and React
            then hydrated one of theirs in its place (a hydration mismatch). */}
        <script dangerouslySetInnerHTML={{ __html: INTRO_GATE_SCRIPT }} />
        <a
          href="#main"
          className="sr-only z-50 rounded-btn bg-accent px-4 py-2 font-medium text-accent-ink focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
        >
          Skip to content
        </a>
        {children}
        <Intro />
      </body>
    </html>
  );
}
