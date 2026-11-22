import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque } from "next/font/google";
import { Intro } from "@/components/intro";
import { INTRO_GATE_SCRIPT } from "@/lib/intro";
import { SITE } from "@/lib/site";
import "./globals.css";

// Display font for headlines, only in the one weight they use (800). The variable font
// (every weight, 41 KB) and its extra axes (opsz, wdth: 131 KB) pushed LCP past 2.5 s
// on Lighthouse's mobile profile.
const display = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
  weight: "800",
});

// Body text uses the system font (globals.css): measured, the Geist web font (30 KB) kept
// LCP above its 2.5 s budget on Lighthouse's phone profile; without it every page passes.

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
      className={`${display.variable} h-full antialiased`}
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
          className="sr-only z-50 rounded-full bg-accent px-4 py-2 font-semibold text-accent-ink focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
        >
          Skip to content
        </a>
        {children}
        <Intro />
      </body>
    </html>
  );
}
