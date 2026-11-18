import type { Metadata } from "next";
import { mediaOptions } from "@/lib/admin/media-options";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveSkill } from "../_lib/actions";
import { SKILL_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New skill" };

export default async function NewSkillPage() {
  return (
    <>
      <PageHeader eyebrow="Skills" title="New skill" back={{ href: "/admin/skills", label: "All skills" }} />
      <ResourceForm fields={SKILL_FIELDS} action={saveSkill.bind(null, null)} media={await mediaOptions()} submitLabel="Create skill" />
    </>
  );
}
