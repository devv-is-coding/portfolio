import type { Metadata } from "next";
import { Suspense } from "react";
import { Pagination } from "@/components/pagination";
import { PosterHeading } from "@/components/poster-heading";
import { PostRow } from "@/components/post-row";
import { PostListSkeleton } from "@/components/skeletons";
import { Container } from "@/components/ui/container";
import { EmptyState } from "@/components/ui/empty-state";
import { Tag } from "@/components/ui/tag";
import { getCategories, getPosts, getTags } from "@/lib/api/public";
import { firstParam, listHref, pageParam } from "@/lib/search-params";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Writing",
  description: `Notes and articles by ${SITE.name}.`,
  alternates: { canonical: "/blog" },
};

const PAGE_SIZE = 10;

export default function BlogPage({ searchParams }: PageProps<"/blog">) {
  return (
    // overflow-x-clip: a row's hover flood runs to the screen's edges, never past them.
    <div className="overflow-x-clip">
      <Container className="flex flex-col gap-12 py-16 sm:py-24">
        <PosterHeading as="h1" title="Writing" />
        {/* The fallback fills the screen, so the footer never jumps when the list streams in. */}
        <Suspense fallback={<PostListSkeleton />}>
          <PostList searchParams={searchParams} />
        </Suspense>
      </Container>
    </div>
  );
}

async function PostList({ searchParams }: Pick<PageProps<"/blog">, "searchParams">) {
  const params = await searchParams;
  const page = pageParam(params.page);
  const category = firstParam(params.category);
  const tag = firstParam(params.tag);
  const [posts, categories, tags] = await Promise.all([
    getPosts({ page, size: PAGE_SIZE, category, tag }),
    getCategories(),
    tag ? getTags() : Promise.resolve([]),
  ]);
  const tagName = tags.find((item) => item.slug === tag)?.name;
  const filtered = Boolean(category || tag);

  // At least a screen tall, like the fallback: a short (empty) list never pulls the footer up.
  return (
    <div className="flex min-h-svh flex-col gap-10">
      {categories.length > 0 && (
        <nav aria-label="Filter by category">
          <ul className="flex flex-wrap gap-2">
            <li>
              <Tag href="/blog" active={!filtered}>
                All
              </Tag>
            </li>
            {categories.map((item) => (
              <li key={item.id}>
                <Tag href={listHref("/blog", { category: item.slug })} active={item.slug === category}>
                  {item.name}
                </Tag>
              </li>
            ))}
          </ul>
        </nav>
      )}
      {tag && (
        <p className="text-muted">
          Posts tagged <span className="text-paper">{tagName ?? tag}</span>.
        </p>
      )}
      {posts.items.length > 0 ? (
        <ul className="border-t border-line">
          {posts.items.map((post, index) => (
            <PostRow key={post.id} post={post} index={index} headingLevel="h2" />
          ))}
        </ul>
      ) : (
        <EmptyState title={filtered || page > 1 ? "No posts here" : "No posts yet"}>
          {filtered || page > 1 ? "Try another filter or the first page." : "The first post is being written."}
        </EmptyState>
      )}
      <Pagination
        page={posts.page}
        pages={posts.pages}
        href={(target) => listHref("/blog", { category, tag, page: target })}
      />
    </div>
  );
}
