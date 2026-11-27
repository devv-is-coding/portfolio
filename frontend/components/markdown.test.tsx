import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { LitMarkdown } from "@/components/markdown";

function render(markdown: string) {
  const html = renderToStaticMarkup(<LitMarkdown>{markdown}</LitMarkdown>);
  const words = [...html.matchAll(/<span class="lit-word" style="--i:(\d+)">(.*?)<\/span>/g)].map((m) => ({
    at: Number(m[1]),
    html: m[2],
  }));
  const text = html.replace(/<[^>]+>/g, "");
  return { html, words, text };
}

describe("LitMarkdown", () => {
  it("wraps every word, placed by its offset in the text, in reading order", () => {
    const { words, text } = render("I build web products.");

    expect(words.map((w) => w.html)).toEqual(["I", "build", "web", "products."]);
    expect(words.map((w) => w.at)).toEqual([0, 2, 8, 12]);
    expect(text).toBe("I build web products.");
  });

  it("lights a link or emphasis as one piece and keeps it working", () => {
    const { words, html } = render("Built with **FastAPI** and [Next.js](https://nextjs.org).");

    expect(words.map((w) => w.html)).toContain("<strong>FastAPI</strong>");
    expect(html).toContain('href="https://nextjs.org"');
    const ats = words.map((w) => w.at);
    expect(ats).toEqual([...ats].sort((a, b) => a - b));
  });

  it("numbers the second paragraph after the first and sets the total on the wrapper", () => {
    const markdown = "First paragraph.\n\nSecond one.";
    const { words, html } = render(markdown);

    expect(words.find((w) => w.html === "Second")?.at).toBe(markdown.indexOf("Second"));
    expect(html).toContain(`style="--n:${markdown.length}"`);
    expect(html.match(/<p /g)).toHaveLength(2);
  });
});
