import type { ComponentProps } from "react";
import { buttonClasses, type ButtonStyle } from "@/components/ui/button-styles";

type ButtonProps = ComponentProps<"button"> & Omit<ButtonStyle, "className">;

export function Button({ variant, size, className, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={buttonClasses({ variant, size, className })} {...props} />;
}
