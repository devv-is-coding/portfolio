import { getProfile, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { platformName } from "@/lib/social";

type QuickLink = { label: string; href: string; external: boolean };

/**
 * The footer's profile details: the social links in their admin order, then email and the
 * résumé, and the place the profile gives. Set in ink on the footer's gold. Nothing
 * without a profile.
 */
export async function ProfileLinks() {
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
  return (
    <div className="flex flex-col gap-3 md:items-end">
      {links.length > 0 && (
        <ul aria-label="Find me elsewhere" className="flex flex-wrap items-center gap-x-6 gap-y-2">
          {links.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                {...(link.external ? { target: "_blank", rel: "noopener noreferrer me" } : {})}
                className="inline-flex items-center justify-center font-semibold underline-offset-4 hover:underline pointer-coarse:min-h-11 pointer-coarse:min-w-11"
              >
                {link.label}
                {link.external && " ↗"}
              </a>
            </li>
          ))}
        </ul>
      )}
      {profile.location && <p className="text-sm">{profile.location}</p>}
    </div>
  );
}
