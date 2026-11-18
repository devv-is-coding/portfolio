import { describe, expect, it } from "vitest";
import { imagekitLoader } from "@/lib/imagekit";

const SRC = "https://ik.imagekit.io/demo/projects/shot.webp";

describe("imagekitLoader", () => {
  it("asks ImageKit for the width, quality and best format", () => {
    const url = new URL(imagekitLoader({ src: SRC, width: 640, quality: 60 }));

    expect(url.origin + url.pathname).toBe(SRC);
    expect(url.searchParams.get("tr")).toBe("w-640,q-60,f-auto");
  });

  it("uses quality 75 by default and keeps other parameters", () => {
    const url = new URL(imagekitLoader({ src: `${SRC}?updatedAt=1`, width: 384 }));

    expect(url.searchParams.get("tr")).toBe("w-384,q-75,f-auto");
    expect(url.searchParams.get("updatedAt")).toBe("1");
  });

  it("replaces a transformation already in the URL", () => {
    const url = new URL(imagekitLoader({ src: `${SRC}?tr=w-9999`, width: 128 }));

    expect(url.searchParams.getAll("tr")).toEqual(["w-128,q-75,f-auto"]);
  });
});
