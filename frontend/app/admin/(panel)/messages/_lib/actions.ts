"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import type { components } from "@/lib/api/schema";
import { MESSAGE_FIELDS } from "./fields";

type Schemas = components["schemas"];

// Messages are never public: no cache tags to refresh.
export async function saveMessageStatus(id: number, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(MESSAGE_FIELDS, formData);
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/contact-messages/{message_id}", {
        params: { path: { message_id: id } },
        body: body as Schemas["ContactMessageUpdate"],
      }),
    tags: [],
    message: "Status saved.",
  });
}

export async function deleteMessage(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/contact-messages/{message_id}", { params: { path: { message_id: id } } }),
    tags: [],
    redirectTo: "/admin/messages",
  });
}
