import type { Metadata } from "next";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminItem, idParam } from "@/lib/admin/reads";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { deleteSkill, saveSkill } from "../_lib/actions";
import { SKILL_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit skill" };

export default async function EditSkillPage({ params }: PageProps<"/admin/skills/[id]">) {
  const id = idParam((await params).id);
  const [skill, media] = await Promise.all([
    adminItem((api) => api.GET("/admin/skills/{skill_id}", { params: { path: { skill_id: id } } })),
    mediaOptions(),
  ]);
  return (
    <>
      <PageHeader
        eyebrow="Skills"
        title={skill.name}
        back={{ href: "/admin/skills", label: "All skills" }}
        action={<DeleteButton action={deleteSkill.bind(null, id)} what={`the skill ${skill.name}`} />}
      />
      <ResourceForm fields={SKILL_FIELDS} action={saveSkill.bind(null, id)} values={skill} media={media} />
    </>
  );
}
