import { describe, expect, it } from "vitest";
import { INTRO_GATE_SCRIPT, INTRO_PLAYED, INTRO_PLAYING, INTRO_SEEN_KEY, INTRO_WAKE } from "@/lib/intro";

type Visit = {
  path?: string;
  reducedMotion?: boolean;
  /** What sessionStorage already holds; `null` stands for storage that throws (blocked). */
  storage?: Map<string, string> | null;
};

/** Runs the gate script against a stand-in browser and reports what it decided. */
function runGate({ path = "/", reducedMotion = false, storage = new Map() }: Visit) {
  const dataset: Record<string, string> = {};
  const sessionStorage = {
    getItem(key: string) {
      if (!storage) {
        throw new Error("SecurityError");
      }
      return storage.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      if (!storage) {
        throw new Error("SecurityError");
      }
      storage.set(key, value);
    },
  };
  const run = new Function("location", "sessionStorage", "matchMedia", "document", INTRO_GATE_SCRIPT);
  run({ pathname: path }, sessionStorage, () => ({ matches: reducedMotion }), { documentElement: { dataset } });
  return { intro: dataset.intro, played: dataset[INTRO_PLAYED], wake: dataset[INTRO_WAKE], storage };
}

describe("intro gate", () => {
  it("plays on the first page of a session and remembers it", () => {
    const { intro, played, storage } = runGate({});

    expect(intro).toBe(INTRO_PLAYING);
    expect(played).toBe("1");
    expect(storage?.get(INTRO_SEEN_KEY)).toBe("1");
  });

  it("marks nothing as played when the greeting doesn't play", () => {
    expect(runGate({ reducedMotion: true }).played).toBeUndefined();
    expect(runGate({ path: "/projects" }).played).toBeUndefined();
  });

  it("stays away on refreshes and later pages of the same session", () => {
    const storage = new Map([[INTRO_SEEN_KEY, "1"]]);

    expect(runGate({ storage }).intro).toBeUndefined();
    expect(runGate({ path: "/projects", storage }).intro).toBeUndefined();
  });

  it("doesn't play when the session starts on another page, and doesn't come later", () => {
    const { intro, storage } = runGate({ path: "/blog/some-post" });

    expect(intro).toBeUndefined();
    expect(storage?.get(INTRO_SEEN_KEY)).toBe("1");
    expect(runGate({ path: "/", storage }).intro).toBeUndefined();
  });

  it("never plays in the admin, and doesn't use up the visit there", () => {
    const { intro, storage } = runGate({ path: "/admin/login" });

    expect(intro).toBeUndefined();
    expect(storage?.has(INTRO_SEEN_KEY)).toBe(false);
  });

  it("never plays with reduced motion, but still wakes the backend", () => {
    const { intro, wake } = runGate({ reducedMotion: true });

    expect(intro).toBeUndefined();
    expect(wake).toBe("1");
  });

  it("wakes the backend on the session's first public page, whichever it is", () => {
    expect(runGate({}).wake).toBe("1");
    expect(runGate({ path: "/projects/some-project" }).wake).toBe("1");
  });

  it("wakes nothing on later pages or in the admin", () => {
    const storage = new Map([[INTRO_SEEN_KEY, "1"]]);

    expect(runGate({ path: "/about", storage }).wake).toBeUndefined();
    expect(runGate({ path: "/admin" }).wake).toBeUndefined();
  });

  it("shows the site at once when storage is blocked, without throwing", () => {
    expect(() => runGate({ storage: null })).not.toThrow();
    expect(runGate({ storage: null }).intro).toBeUndefined();
  });
});
