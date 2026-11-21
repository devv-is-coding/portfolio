import { beforeEach, describe, expect, it, vi } from "vitest";
import { redirect } from "next/navigation";
import { keepPageInRange } from "@/lib/admin/list-pages";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));

describe("keepPageInRange", () => {
  beforeEach(() => {
    vi.mocked(redirect).mockReset();
  });

  it("leaves a page that exists alone", () => {
    keepPageInRange({ page: 2, pages: 3 }, "/admin/media");
    keepPageInRange({ page: 3, pages: 3 }, "/admin/media");

    expect(redirect).not.toHaveBeenCalled();
  });

  it("sends a page past the end to the last page, keeping the filters", () => {
    keepPageInRange({ page: 4, pages: 2 }, "/admin/messages", { status: "unread" });

    expect(redirect).toHaveBeenCalledWith("/admin/messages?status=unread&page=2");
  });

  it("sends a page of an emptied list to the list itself", () => {
    keepPageInRange({ page: 3, pages: 0 }, "/admin/projects");

    expect(redirect).toHaveBeenCalledWith("/admin/projects");
  });

  it("never redirects page 1, even when the list is empty", () => {
    keepPageInRange({ page: 1, pages: 0 }, "/admin/projects");

    expect(redirect).not.toHaveBeenCalled();
  });
});
