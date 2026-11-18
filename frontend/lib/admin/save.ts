import "server-only";
import { refresh, updateTag } from "next/cache";
import { redirect } from "next/navigation";
import type { CacheTag } from "@/lib/api/cache-tags";
import type { ApiClient, ApiResult } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { FormState } from "@/lib/admin/form-state";
import { asAdmin } from "@/lib/auth/session";

/** The form's answer for a refused write; anything else (a redirect, a bug) is rethrown. */
function failure(error: unknown): FormState {
  if (!(error instanceof ApiError)) {
    throw error;
  }
  const fieldErrors = error.fieldErrors();
  const message =
    error.status === 422 && Object.keys(fieldErrors).length > 0
      ? "Please check the highlighted fields."
      : error.message;
  return { status: "failed", error: message, fieldErrors };
}

type WriteOptions<T> = {
  call: (api: ApiClient) => Promise<ApiResult<T>>;
  /** The public data this write changes: refreshed at once with updateTag. */
  tags: readonly CacheTag[];
  /** Where to go afterwards, e.g. a new item's edit page; without it the form says "Saved". */
  redirectTo?: (result: T) => string;
  message?: string;
};

/**
 * Runs an admin write for a form: the API's errors come back as the form's state (field errors
 * included), a success refreshes the affected public pages and redirects or confirms.
 */
export async function adminWrite<T>({ call, tags, redirectTo, message = "Saved." }: WriteOptions<T>): Promise<FormState> {
  let result: T;
  try {
    result = await asAdmin(call);
  } catch (error) {
    return failure(error);
  }
  for (const tag of tags) {
    updateTag(tag);
  }
  if (redirectTo) {
    redirect(redirectTo(result));
  }
  // The admin page itself isn't cached: re-render it, so lists show the change (a new link,
  // gallery image or setting) next to the form's "Saved".
  refresh();
  return { status: "saved", message };
}

type DeleteOptions = {
  call: (api: ApiClient) => Promise<ApiResult<unknown>>;
  tags: readonly CacheTag[];
  /** The list to go back to; without it the current page re-renders (an item of a page). */
  redirectTo?: string;
};

/** Deletes in the API and refreshes the affected public pages. */
export async function adminDelete({ call, tags, redirectTo }: DeleteOptions): Promise<void> {
  await asAdmin(call);
  for (const tag of tags) {
    updateTag(tag);
  }
  if (redirectTo) {
    redirect(redirectTo);
  }
  refresh();
}
