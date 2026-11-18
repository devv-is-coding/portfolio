"use client";

import { useSearchParams } from "next/navigation";
import { useActionState } from "react";
import { Alert } from "@/components/ui/alert";
import { TextField } from "@/components/ui/fields";
import { SubmitButton } from "@/components/ui/submit-button";
import { login, type LoginState } from "@/lib/auth/actions";

export function LoginForm() {
  const [state, action] = useActionState<LoginState, FormData>(login, {});
  const next = useSearchParams().get("next") ?? "";

  return (
    <form action={action} className="flex flex-col gap-6">
      <input type="hidden" name="next" value={next} />
      {state.error && <Alert>{state.error}</Alert>}
      <TextField
        label="Email"
        name="email"
        type="email"
        autoComplete="username"
        required
        defaultValue={state.email}
      />
      <TextField
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        required
      />
      <SubmitButton pendingLabel="Signing in…">Sign in</SubmitButton>
    </form>
  );
}
