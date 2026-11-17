import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";

/** The page width and side padding every section shares. */
export function Container({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("mx-auto w-full max-w-7xl px-5 sm:px-8", className)} {...props} />;
}
