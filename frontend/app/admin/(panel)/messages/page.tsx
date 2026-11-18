import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { Pagination } from "@/components/pagination";
import { Tag } from "@/components/ui/tag";
import { asAdmin } from "@/lib/auth/session";
import { formatDate } from "@/lib/format";
import { firstParam, listHref, pageParam } from "@/lib/search-params";
import { isMessageStatus, MESSAGE_STATUS_OPTIONS } from "./_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Messages" };

const PAGE_SIZE = 25;

export default async function MessagesPage({ searchParams }: PageProps<"/admin/messages">) {
  const params = await searchParams;
  const requested = firstParam(params.status);
  const status = isMessageStatus(requested) ? requested : undefined;
  const page = pageParam(params.page);
  const messages = await asAdmin((api) =>
    api.GET("/admin/contact-messages", { params: { query: { status, page, size: PAGE_SIZE } } }),
  );

  return (
    <>
      <PageHeader eyebrow="Inbox" title="Messages" />
      <nav aria-label="Filter by status" className="mb-6">
        <ul className="flex flex-wrap gap-2">
          <li>
            <Tag href="/admin/messages" active={!status}>
              All
            </Tag>
          </li>
          {MESSAGE_STATUS_OPTIONS.map((option) => (
            <li key={option.value}>
              <Tag href={listHref("/admin/messages", { status: option.value })} active={option.value === status}>
                {option.label}
              </Tag>
            </li>
          ))}
        </ul>
      </nav>
      <DataTable
        items={messages.items}
        href={(message) => `/admin/messages/${message.id}`}
        empty={status ? "No messages with this status" : "No messages yet"}
        columns={[
          { label: "From", value: (message) => message.name },
          { label: "Subject", value: (message) => message.subject ?? "(no subject)" },
          { label: "Received", value: (message) => formatDate(message.created_at) },
          {
            label: "Status",
            value: (message) => (
              <Tag className={message.status === "unread" ? "border-accent text-accent" : undefined}>{message.status}</Tag>
            ),
          },
        ]}
      />
      <div className="mt-8">
        <Pagination
          page={messages.page}
          pages={messages.pages}
          href={(target) => listHref("/admin/messages", { status, page: target })}
        />
      </div>
    </>
  );
}
