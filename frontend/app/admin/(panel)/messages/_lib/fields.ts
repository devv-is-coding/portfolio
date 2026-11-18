import type { Field } from "@/lib/admin/fields";

export const MESSAGE_STATUS_OPTIONS = [
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
  { value: "replied", label: "Replied" },
  { value: "archived", label: "Archived" },
] as const;

export type MessageStatus = (typeof MESSAGE_STATUS_OPTIONS)[number]["value"];

export function isMessageStatus(value: string | undefined): value is MessageStatus {
  return MESSAGE_STATUS_OPTIONS.some((option) => option.value === value);
}

export const MESSAGE_FIELDS: readonly Field[] = [
  { kind: "select", name: "status", label: "Status", required: true, options: MESSAGE_STATUS_OPTIONS },
];
