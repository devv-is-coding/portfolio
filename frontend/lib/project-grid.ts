/**
 * The grid for project cards, by how many there are: three columns left an empty third
 * beside two cards, and a lone card stretched across the page. On paged lists pass the total,
 * not the page's count, so the layout doesn't change between pages.
 */
export function projectGridClass(count: number): string {
  if (count <= 1) {
    return "grid gap-6 md:max-w-xl";
  }
  if (count === 2) {
    return "grid gap-6 md:grid-cols-2";
  }
  return "grid gap-6 md:grid-cols-2 lg:grid-cols-3";
}
