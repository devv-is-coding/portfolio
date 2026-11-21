import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { statusLabel } from "@/lib/admin/options";
import { asAdmin } from "@/lib/auth/session";
import { formatDate } from "@/lib/format";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Posts" };

export default async function PostsAdminPage({ searchParams }: PageProps<"/admin/blog/posts">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/admin/blog/posts", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/blog/posts");
  const { items } = list;
  return (
    <>
      <PageHeader
        eyebrow="Blog"
        title="Posts"
        action={
          <ButtonLink href="/admin/blog/posts/new" size="sm">
            New post
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(post) => `/admin/blog/posts/${post.id}`}
        empty="No posts yet"
        columns={[
          { label: "Title", value: (post) => post.title },
          { label: "Status", value: (post) => statusLabel(post.status) },
          { label: "Category", value: (post) => post.category?.name ?? "—" },
          { label: "Published", value: (post) => (post.published_at ? formatDate(post.published_at) : "—") },
        ]}
      />
      <ListPagination path="/admin/blog/posts" list={list} />
    </>
  );
}
