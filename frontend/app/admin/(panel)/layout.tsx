import Link from "next/link";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth/actions";
import { SITE } from "@/lib/site";
import { AdminNav } from "./_components/admin-nav";

/** The signed-in admin area: navigation on the side (on top on phones), the page beside it. */
export default function PanelLayout({ children }: LayoutProps<"/admin">) {
  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <aside className="flex flex-col gap-6 border-b border-line bg-ink-raised p-4 md:sticky md:top-0 md:h-svh md:w-60 md:border-r md:border-b-0 md:p-6">
        <Link href="/" className="font-display text-xl font-extrabold tracking-tight">
          {SITE.name}
          <span className="text-accent">.</span>
        </Link>
        <AdminNav />
        <form action={logout} className="md:mt-auto">
          <Button type="submit" variant="ghost" size="sm">
            Log out
          </Button>
        </form>
      </aside>
      <main id="main" className="flex-1 px-5 py-8 sm:px-8 lg:px-12">
        {children}
      </main>
    </div>
  );
}
