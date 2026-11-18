import { describe, expect, it } from "vitest";
import { ApiError, toApiError, unreachableError } from "@/lib/api/errors";

describe("toApiError", () => {
  it("reads the API's shared error format", () => {
    const error = toApiError(409, {
      error: { code: "conflict", message: "This slug is taken.", details: null },
    });

    expect(error).toBeInstanceOf(ApiError);
    expect([error.status, error.code, error.message, error.details]).toEqual([
      409,
      "conflict",
      "This slug is taken.",
      [],
    ]);
  });

  it.each([null, "Bad gateway", { detail: "Not Found" }, { error: { code: 1 } }])(
    "falls back to a safe message for an unexpected body (%j)",
    (body) => {
      const error = toApiError(502, body);

      expect([error.status, error.code]).toEqual([502, "unexpected_response"]);
      expect(error.message).toMatch(/unexpected/);
    },
  );
});

describe("ApiError.fieldErrors", () => {
  it("keys messages by field without their location, first message per field", () => {
    const error = toApiError(422, {
      error: {
        code: "validation_error",
        message: "Invalid input.",
        details: [
          { field: "body.email", message: "Not a valid email.", type: "value_error" },
          { field: "body.email", message: "Second message.", type: "value_error" },
          { field: "body.links.0.url", message: "Not a URL.", type: "url_parsing" },
          { field: "query.page", message: "Must be 1 or more.", type: "greater_than_equal" },
          { field: null, message: "Whole body is wrong.", type: null },
        ],
      },
    });

    expect(error.fieldErrors()).toEqual({
      email: "Not a valid email.",
      "links.0.url": "Not a URL.",
      page: "Must be 1 or more.",
    });
  });
});

describe("unreachableError", () => {
  it("is a 503 with a message safe to show", () => {
    const error = unreachableError();

    expect([error.status, error.code]).toEqual([503, "api_unreachable"]);
  });
});
