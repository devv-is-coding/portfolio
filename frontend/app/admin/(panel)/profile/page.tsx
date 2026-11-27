import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminProfile } from "@/lib/admin/reads";
import { deleteSocialLink, saveProfile, saveSocialLink } from "./_lib/actions";
import { PROFILE_FIELDS, SOCIAL_LINK_FIELDS } from "./_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Profile" };

export default async function ProfileAdminPage() {
  const [profile, media] = await Promise.all([adminProfile(), mediaOptions()]);

  return (
    <>
      <PageHeader eyebrow="Content" title="Profile" />
      {!profile && <p className="mb-6 text-muted">There&apos;s no profile yet: the first save creates it.</p>}
      <ResourceForm fields={PROFILE_FIELDS} action={saveProfile} values={profile ?? {}} media={media} submitLabel="Save profile" />

      <section className="mt-16 flex flex-col gap-6 border-t border-line pt-10" aria-labelledby="links-heading">
        <h2 id="links-heading" className="font-display text-2xl">
          Social links
        </h2>
        {profile ? (
          <>
            {profile.social_links.map((link) => (
              <div key={link.id} className="flex flex-col gap-4 rounded-card border border-line p-5">
                <ResourceForm fields={SOCIAL_LINK_FIELDS} action={saveSocialLink.bind(null, link.id)} values={link} submitLabel="Save link" />
                <DeleteButton action={deleteSocialLink.bind(null, link.id)} what={`the ${link.platform} link`} label="Remove" />
              </div>
            ))}
            <h3 className="mt-4 font-semibold">Add a link</h3>
            <ResourceForm fields={SOCIAL_LINK_FIELDS} action={saveSocialLink.bind(null, null)} submitLabel="Add link" />
          </>
        ) : (
          <p className="text-muted">Save the profile first.</p>
        )}
      </section>
    </>
  );
}
