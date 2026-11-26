import { getProfile, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { platformName } from "@/lib/social";

type QuickLink = { label: string; href: string; external: boolean };

/**
 * The hero's quick links, from the profile: the social links in their admin order, then email
 * and the résumé. Nothing without a profile or links; the bar around it keeps its height.
 */
export async function HeroLinks() {
  await readAtRequestTimeWithoutApi();
  const profile = await getProfile();
  if (!profile) {
    return null;
  }
  const links: QuickLink[] = [
    ...profile.social_links.map((link) => ({ label: platformName(link.platform), href: link.url, external: true })),
    ...(profile.email ? [{ label: "Email", href: `mailto:${profile.email}`, external: false }] : []),
    ...(profile.resume ? [{ label: "Résumé", href: profile.resume.url, external: true }] : []),
  ];
  if (links.length === 0) {
    return null;
  }
  return (
    <ul aria-label="Find me elsewhere" className="flex items-center gap-x-8">
      {links.map((link) => (
        <li key={link.href} className="shrink-0">
          <a
            href={link.href}
            {...(link.external ? { target: "_blank", rel: "noopener noreferrer me" } : {})}
            className="font-mono text-xs uppercase tracking-[0.2em] text-muted transition-colors hover:text-accent"
          >
            {link.label}
            {link.external && " ↗"}
          </a>
        </li>
      ))}
    </ul>
  );
}
