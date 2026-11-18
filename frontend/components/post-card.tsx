import Link from "next/link";
import type { PostSummary } from "@/lib/api/public";
import { formatDate } from "@/lib/format";

/** A blog post in a list: date and category, title, excerpt; the whole row links. */
type PostCardProps = {
  post: PostSummary;
  /** `h2` where the posts sit right under the page title, `h3` inside a section. */
  headingLevel?: "h2" | "h3";
};

export function PostCard({ post, headingLevel: Heading = "h3" }: PostCardProps) {
  return (
    <article className="group relative flex flex-col gap-3 border-t border-line py-8">
      <p className="flex flex-wrap gap-x-3 font-mono text-xs uppercase tracking-[0.2em] text-muted">
        {post.published_at && <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>}
        {post.category && <span className="text-accent">{post.category.name}</span>}
      </p>
      <Heading className="font-display text-2xl font-extrabold transition-colors group-hover:text-accent sm:text-3xl">
        <Link href={`/blog/${post.slug}`} className="after:absolute after:inset-0">
          {post.title}
        </Link>
      </Heading>
      {post.excerpt && <p className="max-w-2xl text-muted">{post.excerpt}</p>}
    </article>
  );
}
