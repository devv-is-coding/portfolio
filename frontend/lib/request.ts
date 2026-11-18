import "server-only";
import { headers } from "next/headers";

/**
 * The visitor's IP, as the proxy in front of this server reports it (Vercel, nginx): the last
 * `X-Forwarded-For` entry is the one that proxy wrote; earlier entries come from the client
 * and can be forged. Undefined without a proxy (local development).
 */
export async function clientIp(): Promise<string | undefined> {
  const forwarded = (await headers()).get("x-forwarded-for");
  const last = forwarded?.split(",").at(-1)?.trim();
  return last || undefined;
}
