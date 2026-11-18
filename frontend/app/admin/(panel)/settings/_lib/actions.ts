"use server";

import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";

type JsonValue = components["schemas"]["JsonValue"];
const TAGS = [CACHE_TAGS.settings];

function parseJson(text: string): { ok: true; value: JsonValue } | { ok: false } {
  try {
    return { ok: true, value: JSON.parse(text) as JsonValue };
  } catch {
    return { ok: false };
  }
}

/** Creates or replaces a setting; `key` is bound for an existing one, from the form for a new one. */
export async function saveSetting(boundKey: string | null, _state: FormState, formData: FormData): Promise<FormState> {
  const key = boundKey ?? String(formData.get("key") ?? "").trim();
  const parsed = parseJson(String(formData.get("value") ?? ""));
  if (!parsed.ok) {
    return { status: "failed", error: "Please check the highlighted fields.", fieldErrors: { value: "This isn't valid JSON." } };
  }
  return adminWrite({
    call: (api) => api.PUT("/admin/settings/{key}", { params: { path: { key } }, body: { value: parsed.value } }),
    tags: TAGS,
    message: boundKey === null ? "Setting added." : "Saved.",
  });
}

export async function deleteSetting(key: string): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/settings/{key}", { params: { path: { key } } }),
    tags: TAGS,
  });
}
