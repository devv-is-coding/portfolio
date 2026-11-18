import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button-link";
import { getSkillsForAdmin } from "@/lib/admin/reads";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Skills" };

export default async function SkillsPage() {
  const skills = await getSkillsForAdmin();
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Skills"
        action={
          <ButtonLink href="/admin/skills/new" size="sm">
            New skill
          </ButtonLink>
        }
      />
      <DataTable
        items={skills}
        href={(skill) => `/admin/skills/${skill.id}`}
        empty="No skills yet"
        columns={[
          { label: "Name", value: (skill) => skill.name },
          { label: "Category", value: (skill) => skill.category ?? "—" },
          { label: "Order", value: (skill) => skill.display_order },
        ]}
      />
    </>
  );
}
