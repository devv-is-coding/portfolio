import type { components } from "@/lib/api/schema";

type ErrorBody = components["schemas"]["ErrorBody"];
export type ErrorDetail = components["schemas"]["ErrorDetail"];

/** An error answer from the API, in its shared format `{"error": {code, message, details}}`. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: readonly ErrorDetail[];

  constructor(status: number, body: ErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details ?? [];
  }

  /**
   * Validation messages per form field: `body.email` becomes `email`, nested fields keep
   * their path (`body.links.0.url` becomes `links.0.url`). The first message per field wins.
   */
  fieldErrors(): Record<string, string> {
    const errors: Record<string, string> = {};
    for (const detail of this.details) {
      const field = detail.field?.replace(/^(body|query|path)\./, "");
      if (field && !(field in errors)) {
        errors[field] = detail.message;
      }
    }
    return errors;
  }
}

function isErrorBody(value: unknown): value is ErrorBody {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const { code, message } = value as Record<string, unknown>;
  return typeof code === "string" && typeof message === "string";
}

/** Builds an ApiError from a failed response, even when its body isn't the shared format. */
export function toApiError(status: number, body: unknown): ApiError {
  const error = typeof body === "object" && body !== null ? (body as { error?: unknown }).error : undefined;
  if (isErrorBody(error)) {
    return new ApiError(status, error);
  }
  return new ApiError(status, {
    code: "unexpected_response",
    message: "The API answered in an unexpected way. Please try again.",
  });
}

/** The API couldn't be reached at all (down, wrong API_URL, network). */
export function unreachableError(): ApiError {
  return new ApiError(503, {
    code: "api_unreachable",
    message: "The API can't be reached right now. Please try again in a moment.",
  });
}
