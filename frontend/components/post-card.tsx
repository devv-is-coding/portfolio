import Link from "next/link";
import type { PostSummary } from "@/lib/api/public";
import { formatDate } from "@/lib/format";
import { imagekitLoader } from "@/lib/imagekit";

// The cover that follows the pointer over the row is shown 18rem (288 px) wide: 2x for sharp screens.
const PREVIEW_WIDTH = 640;

/** A blog post in a list: date and category, title, excerpt; the whole row links. */
type PostCardProps = {
  post: PostSummary;
  /** `h2` where the posts sit right under the page title, `h3` inside a section. */
  headingLevel?: "h2" | "h3";
};

export function PostCard({ post, headingLevel: Heading = "h3" }: PostCardProps) {
  return (
    <article
      // With a mouse, the cover follows the pointer over the row (lib/motion/cover-preview.ts).
      data-motion-preview={post.cover ? imagekitLoader({ src: post.cover.url, width: PREVIEW_WIDTH }) : undefined}
      className="group relative flex flex-col gap-3 border-t border-line py-8"
    >
      <p className="flex flex-wrap gap-x-3 font-mono text-xs uppercase tracking-[0.2em] text-muted">
        {post.published_at && <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>}
        {post.category && <span className="text-accent">{post.category.name}</span>}
      </p>
      <Heading className="font-display text-2xl font-extrabold transition-colors group-hover:text-accent">
        <Link href={`/blog/${post.slug}`} className="after:absolute after:inset-0">
          {post.title}
        </Link>
      </Heading>
      {post.excerpt && <p className="max-w-2xl text-muted">{post.excerpt}</p>}
    </article>
  );
}
