import type { Metadata } from "next";
import Link from "next/link";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { asAdmin, currentAdmin } from "@/lib/auth/session";
import { formatDate } from "@/lib/format";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = {
  title: "Dashboard",
};

type Stat = { label: string; value: number; href: string; note?: string };

export default async function DashboardPage() {
  // `size: 1`: only the totals are needed, except for the newest messages shown below.
  const [admin, projects, drafts, posts, skills, unread, recent] = await Promise.all([
    currentAdmin(),
    asAdmin((api) => api.GET("/admin/projects", { params: { query: { size: 1 } } })),
    asAdmin((api) => api.GET("/admin/projects", { params: { query: { size: 1, status: "draft" } } })),
    asAdmin((api) => api.GET("/admin/blog/posts", { params: { query: { size: 1 } } })),
    asAdmin((api) => api.GET("/skills", { params: { query: { size: 1 } } })),
    asAdmin((api) => api.GET("/admin/contact-messages", { params: { query: { size: 1, status: "unread" } } })),
    asAdmin((api) => api.GET("/admin/contact-messages", { params: { query: { size: 5 } } })),
  ]);
  const stats: Stat[] = [
    { label: "Unread messages", value: unread.total, href: "/admin/messages?status=unread" },
    { label: "Projects", value: projects.total, href: "/admin/projects", note: `${drafts.total} draft` },
    { label: "Blog posts", value: posts.total, href: "/admin/blog/posts" },
    { label: "Skills", value: skills.total, href: "/admin/skills" },
  ];

  return (
    <>
      <PageHeader eyebrow={`Signed in as ${admin.email}`} title="Dashboard" />
      <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <li key={stat.label}>
            <Link href={stat.href} className="flex flex-col gap-2 rounded-2xl border border-line bg-ink-raised p-6 transition-colors hover:border-accent">
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{stat.label}</span>
              <span className="font-display text-5xl font-extrabold">{stat.value}</span>
              {stat.note && <span className="text-sm text-muted">{stat.note}</span>}
            </Link>
          </li>
        ))}
      </ul>
      <section className="mt-12 flex flex-col gap-6" aria-labelledby="recent-heading">
        <h2 id="recent-heading" className="font-display text-2xl font-extrabold">
          Newest messages
        </h2>
        <DataTable
          items={recent.items}
          href={(message) => `/admin/messages/${message.id}`}
          empty="No messages yet"
          columns={[
            { label: "From", value: (message) => message.name },
            { label: "Subject", value: (message) => message.subject ?? "(no subject)" },
            { label: "Received", value: (message) => formatDate(message.created_at) },
            { label: "Status", value: (message) => message.status },
          ]}
        />
      </section>
    </>
  );
}
