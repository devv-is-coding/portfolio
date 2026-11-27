import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Markdown } from "@/components/markdown";
import { MediaImage } from "@/components/media-image";
import { ArticleSkeleton } from "@/components/skeletons";
import { Container } from "@/components/ui/container";
import { Tag } from "@/components/ui/tag";
import { getPost } from "@/lib/api/public";
import { formatDate } from "@/lib/format";
import { listHref } from "@/lib/search-params";

export async function generateMetadata({ params }: PageProps<"/blog/[slug]">): Promise<Metadata> {
  const post = await getPost((await params).slug);
  if (!post) {
    return { title: "Post not found" };
  }
  return {
    title: post.title,
    description: post.excerpt ?? undefined,
    alternates: { canonical: `/blog/${post.slug}` },
    openGraph: {
      type: "article",
      publishedTime: post.published_at ?? undefined,
      images: post.cover ? [post.cover.url] : undefined,
    },
  };
}

/** Not prerendered per slug: the first visit renders and caches it (no API needed at build). */
export default function PostPage({ params }: PageProps<"/blog/[slug]">) {
  return (
    <Suspense fallback={<ArticleSkeleton narrow />}>
      <PostArticle params={params} />
    </Suspense>
  );
}

async function PostArticle({ params }: Pick<PageProps<"/blog/[slug]">, "params">) {
  const post = await getPost((await params).slug);
  if (!post) {
    notFound();
  }
  const { cover } = post;

  return (
    <article>
      <Container className="flex flex-col gap-12 py-16 sm:py-24">
        <Link href="/blog" className="inline-flex w-fit items-center text-sm font-semibold text-muted hover:text-accent pointer-coarse:min-h-11">
          ← All posts
        </Link>
        <header className="flex max-w-5xl flex-col gap-8">
          <p className="flex flex-wrap gap-x-4 text-sm font-semibold text-muted">
            {post.published_at && <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>}
            {post.category && (
              <Link href={listHref("/blog", { category: post.category.slug })} className="text-accent hover:underline">
                {post.category.name}
              </Link>
            )}
          </p>
          <h1 className="font-display text-[clamp(2.75rem,6.5vw,6rem)] leading-[0.9] tracking-[-0.035em]">{post.title}</h1>
          {post.excerpt && <p className="max-w-2xl text-xl leading-relaxed text-muted">{post.excerpt}</p>}
        </header>
        {cover && (
          <div className="overflow-hidden rounded-card border border-line">
            <MediaImage
              src={cover.url}
              alt={cover.alt_text ?? ""}
              width={cover.width}
              height={cover.height}
              sizes="(min-width: 1280px) 1216px, 100vw"
              fetchPriority="high"
              loading="eager"
              className="block h-auto w-full"
            />
          </div>
        )}
        {/* A reading measure: the text column stays narrow under the wide title. */}
        <div className="flex max-w-3xl flex-col gap-10">
          <Markdown className="text-lg">{post.content}</Markdown>
          {post.tags.length > 0 && (
            <ul className="flex flex-wrap gap-2 border-t border-line pt-8" aria-label="Tags">
              {post.tags.map((tag) => (
                <li key={tag.id}>
                  <Tag href={listHref("/blog", { tag: tag.slug })}>{tag.name}</Tag>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Container>
    </article>
  );
}
