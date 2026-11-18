import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Markdown } from "@/components/markdown";
import { MediaImage } from "@/components/media-image";
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
    <Suspense fallback={<Container className="h-[60vh] py-24" />}>
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
      <Container className="flex max-w-3xl flex-col gap-10 py-16 sm:py-24">
        <Link href="/blog" className="w-fit font-mono text-xs uppercase tracking-[0.2em] text-muted hover:text-accent">
          ← All posts
        </Link>
        <header className="flex flex-col gap-6">
          <p className="flex flex-wrap gap-x-3 font-mono text-xs uppercase tracking-[0.2em] text-muted">
            {post.published_at && <time dateTime={post.published_at}>{formatDate(post.published_at)}</time>}
            {post.category && (
              <Link href={listHref("/blog", { category: post.category.slug })} className="text-accent hover:underline">
                {post.category.name}
              </Link>
            )}
          </p>
          <h1 className="font-display text-headline font-extrabold uppercase">{post.title}</h1>
          {post.excerpt && <p className="text-xl text-muted">{post.excerpt}</p>}
        </header>
        {cover && (
          <MediaImage
            src={cover.url}
            alt={cover.alt_text ?? ""}
            width={cover.width}
            height={cover.height}
            sizes="(min-width: 768px) 768px, 100vw"
            fetchPriority="high"
            loading="eager"
            className="h-auto w-full rounded-2xl border border-line"
          />
        )}
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
      </Container>
    </article>
  );
}
