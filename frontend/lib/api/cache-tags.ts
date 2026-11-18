/**
 * One cache tag per public resource. Cached public reads (`"use cache"`) tag themselves with
 * one of these; admin writes refresh the tags they affect with `updateTag`, so visitors see a
 * change on their next request instead of after the cache lifetime.
 */
export const CACHE_TAGS = {
  profile: "profile",
  skills: "skills",
  projects: "projects",
  experiences: "experiences",
  education: "education",
  certifications: "certifications",
  blog: "blog",
  settings: "settings",
} as const;

export type CacheTag = (typeof CACHE_TAGS)[keyof typeof CACHE_TAGS];
