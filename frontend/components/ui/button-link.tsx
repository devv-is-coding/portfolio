import Link from "next/link";
import type { ComponentProps } from "react";
import { buttonClasses, type ButtonStyle } from "@/components/ui/button-styles";

type ButtonLinkProps = ComponentProps<typeof Link> & Omit<ButtonStyle, "className">;

/** A link styled as a button: the site's calls to action. */
export function ButtonLink({ variant, size, className, ...props }: ButtonLinkProps) {
  return <Link className={buttonClasses({ variant, size, className })} {...props} />;
}
