import type { Metadata } from "next";
import { Eyebrow } from "@/components/ui/eyebrow";
import { currentAdmin } from "@/lib/auth/session";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default async function DashboardPage() {
  const admin = await currentAdmin();

  return (
    <div className="flex flex-col gap-4">
      <Eyebrow>Dashboard</Eyebrow>
      <h1 className="font-display text-headline font-extrabold uppercase">Welcome back</h1>
      <p className="text-muted">Signed in as {admin.email}.</p>
    </div>
  );
}
