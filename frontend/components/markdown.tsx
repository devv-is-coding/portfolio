import type { ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { MediaImage } from "@/components/media-image";
import { cn } from "@/lib/cn";

// Raw HTML in the Markdown is never rendered (react-markdown escapes it) and unsafe link
// targets such as `javascript:` are dropped, so content from the API can't inject scripts.
const COMPONENTS: Components = {
  p: ({ children }) => <p className="mt-5 leading-relaxed text-paper/90">{children}</p>,
  a: ({ href, children }) => {
    const external = href?.startsWith("http");
    return (
      <a
        href={href}
        className="text-accent underline decoration-accent/40 underline-offset-4 hover:decoration-accent"
        {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      >
        {children}
      </a>
    );
  },
  ul: ({ children }) => <ul className="mt-5 list-disc space-y-2 pl-6 marker:text-accent">{children}</ul>,
  ol: ({ children }) => <ol className="mt-5 list-decimal space-y-2 pl-6 marker:text-muted">{children}</ol>,
  blockquote: ({ children }) => (
    <blockquote className="mt-6 border-l-2 border-accent pl-5 text-muted italic">{children}</blockquote>
  ),
  code: ({ className, children }) => (
    <code className={cn("rounded bg-ink-raised px-1.5 py-0.5 font-mono text-[0.9em]", className)}>{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="mt-6 overflow-x-auto rounded-xl border border-line bg-ink-raised p-5 text-sm [&_code]:bg-transparent [&_code]:p-0">
      {children}
    </pre>
  ),
  hr: () => <hr className="my-10 border-line" />,
  table: ({ children }) => (
    <div className="mt-6 overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border-b border-line px-3 py-2 font-semibold">{children}</th>,
  td: ({ children }) => <td className="border-b border-line px-3 py-2">{children}</td>,
  img: ({ src, alt }) =>
    typeof src === "string" ? (
      <MediaImage src={src} alt={alt ?? ""} width={null} height={null} sizes="(min-width: 768px) 720px, 100vw" className="mt-6 h-auto w-full rounded-xl" />
    ) : null,
};

type Level = 2 | 3 | 4 | 5 | 6;

const HEADING_STYLES: Record<Level, string> = {
  2: "mt-12 font-display text-3xl font-extrabold uppercase",
  3: "mt-10 font-display text-2xl font-extrabold",
  4: "mt-8 text-lg font-semibold",
  5: "mt-6 font-semibold",
  6: "mt-6 font-semibold text-muted",
};

/** Headings never go above `min`, so they nest under the page's own headings. */
function headings(min: Level): Components {
  const at = (level: number) => {
    const rendered = Math.min(6, Math.max(level, min)) as Level;
    const Heading = `h${rendered}` as const;
    function MarkdownHeading({ children }: { children?: ReactNode }) {
      return <Heading className={HEADING_STYLES[rendered]}>{children}</Heading>;
    }
    return MarkdownHeading;
  };
  return { h1: at(1), h2: at(2), h3: at(3), h4: at(4), h5: at(5), h6: at(6) };
}

const BY_MIN_LEVEL = { 2: headings(2), 4: headings(4) } as const;

type MarkdownProps = {
  children: string;
  /** The highest heading level inside: 2 under a page title, 4 inside an entry with an h3. */
  minHeading?: keyof typeof BY_MIN_LEVEL;
  className?: string;
};

/** Markdown from the API (biography, descriptions, blog posts), styled for the site. */
export function Markdown({ children, minHeading = 2, className }: MarkdownProps) {
  return (
    <div className={cn("[&>*:first-child]:mt-0", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ ...COMPONENTS, ...BY_MIN_LEVEL[minHeading] }}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
