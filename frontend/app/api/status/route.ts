import { connection } from "next/server";
import { serviceStatus } from "@/lib/api/status";

/**
 * `{ "status": "ok" | "database_down" | "api_down" }`, for the error screens: in production the
 * browser never sees why a server render failed, so they ask here. Checked on every request.
 */
export async function GET() {
  await connection();
  return Response.json({ status: await serviceStatus() }, { headers: { "Cache-Control": "no-store" } });
}
