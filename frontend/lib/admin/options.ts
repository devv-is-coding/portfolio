/** The API's publication statuses: drafts and archived items never show on the site. */
export const PUBLICATION_STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "published", label: "Published" },
  { value: "archived", label: "Archived" },
] as const;

export function statusLabel(status: string): string {
  return PUBLICATION_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
}
