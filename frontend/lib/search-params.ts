type ParamValue = string | string[] | undefined;

/** The first value of a query parameter (`?tag=a&tag=b` gives `a`), or undefined. */
export function firstParam(value: ParamValue): string | undefined {
  const first = Array.isArray(value) ? value[0] : value;
  return first?.trim() || undefined;
}

/** A page number from the URL: a whole number of 1 or more, otherwise 1. */
export function pageParam(value: ParamValue): number {
  const page = Number(firstParam(value));
  return Number.isInteger(page) && page >= 1 ? page : 1;
}

/** A list URL with its filters; empty values and page 1 are left out. */
export function listHref(path: string, params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "" && !(key === "page" && value === 1)) {
      query.set(key, String(value));
    }
  }
  const search = query.toString();
  return search ? `${path}?${search}` : path;
}
