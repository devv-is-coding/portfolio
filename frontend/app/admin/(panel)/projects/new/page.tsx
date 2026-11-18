import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { mediaOptions } from "@/lib/admin/media-options";
import { saveProject } from "../_lib/actions";
import { PROJECT_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New project" };

export default async function NewProjectPage() {
  return (
    <>
      <PageHeader eyebrow="Projects" title="New project" back={{ href: "/admin/projects", label: "All projects" }} />
      <ResourceForm
        fields={PROJECT_FIELDS}
        action={saveProject.bind(null, null)}
        values={{ status: "draft" }}
        media={await mediaOptions()}
        submitLabel="Create project"
      />
    </>
  );
}
