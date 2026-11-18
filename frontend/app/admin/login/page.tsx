import type { Metadata } from "next";
import { Suspense } from "react";
import { Eyebrow } from "@/components/ui/eyebrow";
import { LoginForm } from "./_components/login-form";

export const metadata: Metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return (
    <main id="main" className="flex flex-1 items-center justify-center px-5 py-16">
      <div className="flex w-full max-w-sm flex-col gap-8">
        <div className="flex flex-col gap-4">
          <Eyebrow>Admin</Eyebrow>
          <h1 className="font-display text-headline font-extrabold uppercase">Sign in</h1>
        </div>
        {/* The form reads ?next= from the URL, which only exists at request time. */}
        <Suspense>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
