import { describe, expect, it } from "vitest";
import { mapWithConcurrency } from "@/lib/concurrency";

/** Resolves after the given milliseconds, recording how many tasks run at once. */
function tracker() {
  let running = 0;
  let peak = 0;
  return {
    get peak() {
      return peak;
    },
    async run<T>(value: T, ms: number): Promise<T> {
      running += 1;
      peak = Math.max(peak, running);
      await new Promise((resolve) => setTimeout(resolve, ms));
      running -= 1;
      return value;
    },
  };
}

describe("mapWithConcurrency", () => {
  it("keeps the items' order, whatever order the tasks finish in", async () => {
    const work = tracker();

    const results = await mapWithConcurrency([30, 5, 15, 1], 2, (ms, index) => work.run(index, ms));

    expect(results).toEqual([0, 1, 2, 3]);
  });

  it("never runs more than the limit at once", async () => {
    const work = tracker();

    await mapWithConcurrency(Array.from({ length: 7 }, (_, i) => i), 3, (i) => work.run(i, 5));

    expect(work.peak).toBe(3);
  });

  it("runs everything at once when there are fewer items than the limit", async () => {
    const work = tracker();

    const results = await mapWithConcurrency(["a", "b"], 3, (item) => work.run(item, 5));

    expect(results).toEqual(["a", "b"]);
    expect(work.peak).toBe(2);
  });

  it("returns nothing for no items", async () => {
    expect(await mapWithConcurrency([], 3, async () => 1)).toEqual([]);
  });
});
