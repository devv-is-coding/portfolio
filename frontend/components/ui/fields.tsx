import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/cn";

const CONTROL =
  "w-full rounded-xl border border-line bg-ink px-4 py-3 text-paper transition-colors placeholder:text-muted/60 hover:border-paper/30 aria-invalid:border-signal";

type FieldFrameProps = {
  id: string;
  label: string;
  error?: string;
  hint?: string;
  className?: string;
  children: ReactNode;
};

/** Label, control, then the hint or the error, wired up with aria-describedby. */
function FieldFrame({ id, label, error, hint, className, children }: FieldFrameProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-message`} className="text-sm text-signal">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-message`} className="text-sm text-muted">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

// `id` defaults to `field-<name>`; pages with several forms pass their own, unique ones.
type OwnProps = { label: string; name: string; error?: string; hint?: string; id?: string };

function controlProps(name: string, error?: string, hint?: string, ownId?: string) {
  const id = ownId ?? `field-${name}`;
  return {
    id,
    name,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error || hint ? `${id}-message` : undefined,
  };
}

export function TextField({ label, name, error, hint, id, className, ...props }: ComponentProps<"input"> & OwnProps) {
  const control = controlProps(name, error, hint, id);
  return (
    <FieldFrame id={control.id} label={label} error={error} hint={hint} className={className}>
      <input className={CONTROL} {...control} {...props} />
    </FieldFrame>
  );
}

export function TextAreaField({ label, name, error, hint, id, className, ...props }: ComponentProps<"textarea"> & OwnProps) {
  const control = controlProps(name, error, hint, id);
  return (
    <FieldFrame id={control.id} label={label} error={error} hint={hint} className={className}>
      <textarea className={cn(CONTROL, "min-h-40")} {...control} {...props} />
    </FieldFrame>
  );
}

export function SelectField({ label, name, error, hint, id, className, children, ...props }: ComponentProps<"select"> & OwnProps) {
  const control = controlProps(name, error, hint, id);
  return (
    <FieldFrame id={control.id} label={label} error={error} hint={hint} className={className}>
      <select className={CONTROL} {...control} {...props}>
        {children}
      </select>
    </FieldFrame>
  );
}

export function CheckboxField({ label, name, error, hint, id, className, ...props }: Omit<ComponentProps<"input">, "type"> & OwnProps) {
  const control = controlProps(name, error, hint, id);
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label htmlFor={control.id} className="flex items-center gap-3 text-sm font-semibold">
        <input type="checkbox" className="size-5 accent-accent" {...control} {...props} />
        {label}
      </label>
      {(error || hint) && (
        <p id={`${control.id}-message`} className={cn("text-sm", error ? "text-signal" : "text-muted")}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}
