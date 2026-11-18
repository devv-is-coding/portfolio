import "server-only";
import { cacheLife, cacheTag } from "next/cache";
import { connection } from "next/server";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import { apiClient, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

/*
 * Cached reads of the public API, for Server Components. Each is cached for hours under its
 * resource's tag; admin writes refresh the tag (updateTag), so changes show up at once.
 * A failed read throws (never cached): a background revalidation then keeps the last good
 * page, and a first visit gets the error page instead of an empty one.
 */

type Schemas = components["schemas"];
export type Profile = Schemas["ProfileRead"];
export type ProjectSummary = Schemas["ProjectSummary"];
export type ProjectDetail = Schemas["ProjectDetail"];
export type Skill = Schemas["SkillRead"];
export type Experience = Schemas["ExperienceRead"];
export type Education = Schemas["EducationRead"];
export type Certification = Schemas["CertificationRead"];
export type PostSummary = Schemas["BlogPostSummary"];
export type PostDetail = Schemas["BlogPostDetail"];
export type BlogTerm = Schemas["BlogTermRead"];
export type Media = Schemas["PublicMedia"];
export type Page<T> = { items: T[]; total: number; page: number; size: number; pages: number };

// The API's largest page: lists the site shows whole (skills, timeline) fit in one.
const ALL = 100;

/**
 * Data components call this first. Without API_URL at build time (CI, Docker image builds)
 * nothing can be prerendered, so the data is read per request instead (still cached).
 * With API_URL (local builds, Vercel) the pages prerender with their data.
 */
export async function readAtRequestTimeWithoutApi(): Promise<void> {
  if (!process.env.API_URL) {
    await connection();
  }
}

function nullIfNotFound(error: unknown): null {
  if (error instanceof ApiError && error.status === 404) {
    return null;
  }
  throw error;
}

/** The profile, or null until the admin has created it. */
export async function getProfile(): Promise<Profile | null> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.profile);
  return unwrap(apiClient().GET("/profile")).catch(nullIfNotFound);
}

export type ProjectQuery = { page?: number; size?: number; featured?: boolean; skill?: string };

export async function getProjects(query: ProjectQuery = {}): Promise<Page<ProjectSummary>> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.projects);
  return unwrap(apiClient().GET("/projects", { params: { query } }));
}

/** A published project, or null for an unknown, draft or archived one. */
export async function getProject(slug: string): Promise<ProjectDetail | null> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.projects);
  return unwrap(apiClient().GET("/projects/{slug}", { params: { path: { slug } } })).catch(
    nullIfNotFound,
  );
}

export async function getSkills(): Promise<Skill[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.skills);
  const page = await unwrap(apiClient().GET("/skills", { params: { query: { size: ALL } } }));
  return page.items;
}

export async function getExperiences(): Promise<Experience[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.experiences);
  const page = await unwrap(apiClient().GET("/experiences", { params: { query: { size: ALL } } }));
  return page.items;
}

export async function getEducation(): Promise<Education[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.education);
  const page = await unwrap(apiClient().GET("/education", { params: { query: { size: ALL } } }));
  return page.items;
}

export async function getCertifications(): Promise<Certification[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.certifications);
  const page = await unwrap(
    apiClient().GET("/certifications", { params: { query: { size: ALL } } }),
  );
  return page.items;
}

export type PostQuery = { page?: number; size?: number; category?: string; tag?: string };

export async function getPosts(query: PostQuery = {}): Promise<Page<PostSummary>> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.blog);
  return unwrap(apiClient().GET("/blog/posts", { params: { query } }));
}

/** A published post, or null for an unknown, draft or archived one. */
export async function getPost(slug: string): Promise<PostDetail | null> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.blog);
  return unwrap(apiClient().GET("/blog/posts/{slug}", { params: { path: { slug } } })).catch(
    nullIfNotFound,
  );
}

export async function getCategories(): Promise<BlogTerm[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.blog);
  const page = await unwrap(
    apiClient().GET("/blog/categories", { params: { query: { size: ALL } } }),
  );
  return page.items;
}

export async function getTags(): Promise<BlogTerm[]> {
  "use cache";
  cacheLife("hours");
  cacheTag(CACHE_TAGS.blog);
  const page = await unwrap(
    apiClient().GET("/blog/tags", { params: { query: { size: ALL } } }),
  );
  return page.items;
}
