import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ChecklistForm } from "@/components/admin/checklist-form";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { MediaImage } from "@/components/media-image";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminItem, getSkillsForAdmin, idParam } from "@/lib/admin/reads";
import {
  addProjectImage,
  deleteProject,
  deleteProjectImage,
  saveProject,
  saveProjectImage,
  saveProjectSkills,
} from "../_lib/actions";
import { IMAGE_ADD_FIELDS, IMAGE_EDIT_FIELDS, PROJECT_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit project" };

const SECTION = "mt-16 flex flex-col gap-6 border-t border-line pt-10";

export default async function EditProjectPage({ params }: PageProps<"/admin/projects/[id]">) {
  const id = idParam((await params).id);
  const [project, skills, media] = await Promise.all([
    adminItem((api) => api.GET("/admin/projects/{project_id}", { params: { path: { project_id: id } } })),
    getSkillsForAdmin(),
    mediaOptions(),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Projects"
        title={project.title}
        back={{ href: "/admin/projects", label: "All projects" }}
        action={<DeleteButton action={deleteProject.bind(null, id)} what={`the project ${project.title} and its gallery`} />}
      />
      <ResourceForm fields={PROJECT_FIELDS} action={saveProject.bind(null, id)} values={project} media={media} />

      <section className={SECTION} aria-labelledby="skills-heading">
        <h2 id="skills-heading" className="font-display text-2xl font-extrabold">Skills</h2>
        <ChecklistForm
          legend="Skills used in this project"
          options={skills.map((skill) => ({ id: skill.id, label: skill.name }))}
          selected={project.skills.map((skill) => skill.id)}
          action={saveProjectSkills.bind(null, id)}
          submitLabel="Save skills"
          empty="No skills yet: add them under Skills first."
        />
      </section>

      <section className={SECTION} aria-labelledby="gallery-heading">
        <h2 id="gallery-heading" className="font-display text-2xl font-extrabold">Gallery</h2>
        {project.images.map((item) => (
          <div key={item.id} className="grid gap-6 rounded-2xl border border-line p-5 md:grid-cols-[12rem_1fr]">
            <MediaImage
              src={item.image.url}
              alt={item.image.alt_text ?? ""}
              width={item.image.width}
              height={item.image.height}
              sizes="192px"
              className="h-auto w-full rounded-lg"
            />
            <div className="flex flex-col gap-4">
              <ResourceForm
                fields={IMAGE_EDIT_FIELDS}
                action={saveProjectImage.bind(null, id, item.id)}
                values={{ alt_text: item.image.alt_text, display_order: item.display_order }}
                submitLabel="Save image"
              />
              <DeleteButton action={deleteProjectImage.bind(null, id, item.id)} what="this image from the gallery" label="Remove" />
            </div>
          </div>
        ))}
        <h3 className="mt-4 font-semibold">Add an image</h3>
        <ResourceForm fields={IMAGE_ADD_FIELDS} action={addProjectImage.bind(null, id)} media={media} submitLabel="Add image" />
      </section>
    </>
  );
}
