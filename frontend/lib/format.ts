// Dates from the API are ISO strings: `2024-03-01` (dates) or `2024-03-01T10:00:00` (UTC
// timestamps). They are formatted in UTC, so the server's time zone never shifts a day.
const MONTH_YEAR = new Intl.DateTimeFormat("en", { month: "short", year: "numeric", timeZone: "UTC" });
const FULL_DATE = new Intl.DateTimeFormat("en", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

/** An API date or timestamp as a Date. */
export function parseApiDate(value: string): Date {
  // A date-only value would otherwise be read as UTC midnight already; timestamps from the
  // API are naive UTC, so mark them as UTC explicitly.
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) || value.length === 10 ? value : `${value}Z`);
}

/** `Mar 2024` */
export function formatMonthYear(value: string): string {
  return MONTH_YEAR.format(parseApiDate(value));
}

/** `March 1, 2024` */
export function formatDate(value: string): string {
  return FULL_DATE.format(parseApiDate(value));
}

/** `Mar 2021 – Present`, `Mar 2021 – Jan 2024`, or just the known end. */
export function formatPeriod(start: string | null, end: string | null, ongoingLabel = "Present"): string {
  const to = end ? formatMonthYear(end) : ongoingLabel;
  return start ? `${formatMonthYear(start)} – ${to}` : to;
}
