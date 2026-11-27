import Link from "next/link";
import type { CSSProperties } from "react";
import type { PostSummary } from "@/lib/api/public";
import { formatDate } from "@/lib/format";

type PostRowProps = {
  post: PostSummary;
  /** Its place in the list: staggers the scroll entrance. */
  index: number;
  /** `h2` where the rows sit right under the page title (/blog), `h3` inside a section (home). */
  headingLevel?: "h2" | "h3";
};

/**
 * A post as a huge-title row (date and category, title, a short excerpt) that floods with
 * marigold on hover (`.flood-row`, globals.css); the whole row links to the post. The list
 * around it needs `overflow-x-clip` (the flood runs to the screen's edges) and a top border.
 */
export function PostRow({ post, index, headingLevel: Heading = "h3" }: PostRowProps) {
  return (
    <li
      data-reveal
      style={{ "--reveal": index } as CSSProperties}
      className="flood-row relative isolate grid gap-3 border-b border-line py-7 md:grid-cols-[9rem_minmax(0,1fr)_minmax(0,20rem)] md:items-center md:gap-8 md:py-9"
    >
      <p className="flood-soft text-sm font-semibold text-muted">
        {post.published_at && <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>}
        {post.category && <span className="block">{post.category.name}</span>}
      </p>
      <Heading className="flood-title font-display text-[clamp(2rem,4vw,3.75rem)] leading-[0.92] tracking-[-0.03em]">
        {/* The whole row is the link (its box covers the row). */}
        <Link href={`/blog/${post.slug}`} className="after:absolute after:inset-0">
          {post.title}
        </Link>
      </Heading>
      {post.excerpt && <p className="flood-soft line-clamp-2 leading-relaxed text-muted">{post.excerpt}</p>}
    </li>
  );
}
