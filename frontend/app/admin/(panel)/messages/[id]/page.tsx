import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { ButtonLink } from "@/components/ui/button-link";
import { adminItem, idParam } from "@/lib/admin/reads";
import { formatDate } from "@/lib/format";
import { deleteMessage, saveMessageStatus } from "../_lib/actions";
import { MESSAGE_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Message" };

export default async function MessagePage({ params }: PageProps<"/admin/messages/[id]">) {
  const id = idParam((await params).id);
  const message = await adminItem((api) =>
    api.GET("/admin/contact-messages/{message_id}", { params: { path: { message_id: id } } }),
  );
  const subject = message.subject ?? "(no subject)";
  const reply = `mailto:${message.email}?subject=${encodeURIComponent(`Re: ${message.subject ?? "your message"}`)}`;

  return (
    <>
      <PageHeader
        eyebrow="Message"
        title={subject}
        back={{ href: "/admin/messages", label: "All messages" }}
        action={<DeleteButton action={deleteMessage.bind(null, id)} what={`the message from ${message.name}`} />}
      />
      <dl className="mb-8 grid max-w-3xl gap-x-8 gap-y-2 text-sm sm:grid-cols-[8rem_1fr]">
        <dt className="text-muted">From</dt>
        <dd>
          {message.name} &lt;{message.email}&gt;
        </dd>
        <dt className="text-muted">Received</dt>
        <dd>{formatDate(message.created_at)}</dd>
        {message.ip_address && (
          <>
            <dt className="text-muted">IP address</dt>
            <dd className="font-mono">{message.ip_address}</dd>
          </>
        )}
      </dl>
      {/* Plain text from a visitor: rendered as text (React escapes it), keeping line breaks. */}
      <p className="mb-8 max-w-3xl rounded-card border border-line bg-ink-raised p-6 whitespace-pre-wrap">{message.message}</p>
      <ButtonLink href={reply} variant="secondary" size="sm" className="mb-10">
        Reply by email
      </ButtonLink>
      <ResourceForm fields={MESSAGE_FIELDS} action={saveMessageStatus.bind(null, id)} values={message} submitLabel="Save status" />
    </>
  );
}
