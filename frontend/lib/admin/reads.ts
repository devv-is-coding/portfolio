import "server-only";
import { notFound } from "next/navigation";
import type { ApiClient, ApiResult } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { asAdmin } from "@/lib/auth/session";

/** A numeric id from the URL, or the 404 page for anything else. */
export function idParam(value: string): number {
  const id = Number(value);
  if (!Number.isInteger(id) || id < 1) {
    notFound();
  }
  return id;
}

/** An item for an admin page; an unknown id shows the 404 page. */
export async function adminItem<T>(call: (api: ApiClient) => Promise<ApiResult<T>>): Promise<T> {
  try {
    return await asAdmin(call);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

// The API's largest page; a portfolio's lists fit in it.
const ALL = 100;

export function getSkillsForAdmin() {
  return asAdmin((api) => api.GET("/skills", { params: { query: { size: ALL } } })).then((page) => page.items);
}

export function getCategoriesForAdmin() {
  return asAdmin((api) => api.GET("/blog/categories", { params: { query: { size: ALL } } })).then((page) => page.items);
}

export function getTagsForAdmin() {
  return asAdmin((api) => api.GET("/blog/tags", { params: { query: { size: ALL } } })).then((page) => page.items);
}

/** The profile for editing (not the cached public read), or null before the first save. */
export async function adminProfile() {
  try {
    return await asAdmin((api) => api.GET("/profile"));
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}
