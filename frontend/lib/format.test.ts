import { describe, expect, it } from "vitest";
import { formatDate, formatMonthYear, formatPeriod, formatWorkPeriod } from "@/lib/format";

describe("dates", () => {
  it("formats dates and naive UTC timestamps without shifting the day", () => {
    expect(formatMonthYear("2024-03-01")).toBe("Mar 2024");
    expect(formatDate("2024-03-01")).toBe("March 1, 2024");
    expect(formatDate("2024-03-31T23:30:00")).toBe("March 31, 2024");
    expect(formatDate("2024-03-31T23:30:00Z")).toBe("March 31, 2024");
  });

  it("formats a period, open or closed", () => {
    expect(formatPeriod("2021-03-01", null)).toBe("Mar 2021 – Present");
    expect(formatPeriod("2021-03-01", "2024-01-15")).toBe("Mar 2021 – Jan 2024");
    expect(formatPeriod(null, "2019-06-30")).toBe("Jun 2019");
    expect(formatPeriod("2015-04-01", null, "In progress")).toBe("Apr 2015 – In progress");
  });

  it("formats a project's work period, or nothing without dates", () => {
    expect(formatWorkPeriod("2025-03-01", "2025-06-30")).toBe("Mar 2025 – Jun 2025");
    expect(formatWorkPeriod("2025-03-01", "2025-03-28")).toBe("Mar 2025");
    expect(formatWorkPeriod("2025-03-01", null)).toBe("Mar 2025 – Present");
    expect(formatWorkPeriod(null, "2025-06-30")).toBe("Jun 2025");
    expect(formatWorkPeriod(null, null)).toBeNull();
  });
});
