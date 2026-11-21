import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ChecklistForm } from "@/components/admin/checklist-form";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { MediaImage } from "@/components/media-image";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminItem, getSkillsForAdmin, idParam } from "@/lib/admin/reads";
import { GalleryPicker } from "../_components/gallery-picker";
import {
  addProjectImages,
  deleteProject,
  deleteProjectImage,
  saveProject,
  saveProjectImage,
  saveProjectSkills,
} from "../_lib/actions";
import { IMAGE_EDIT_FIELDS, PROJECT_FIELDS } from "../_lib/fields";

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
  const inGallery = new Set(project.images.map((item) => item.media_id));
  // New pictures go after the last one.
  const nextOrder = Math.max(-1, ...project.images.map((item) => item.display_order)) + 1;

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
        {project.images.length > 0 && (
          // Three to a row on wide screens, so a long gallery takes a few rows, not a long scroll.
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {project.images.map((item) => (
              <li key={item.id} className="flex flex-col gap-4 rounded-2xl border border-line p-4">
                <MediaImage
                  src={item.image.url}
                  alt={item.image.alt_text ?? ""}
                  width={item.image.width}
                  height={item.image.height}
                  sizes="(min-width: 1024px) 320px, (min-width: 640px) 45vw, 100vw"
                  className="aspect-[4/3] w-full rounded-lg bg-ink-raised object-contain"
                />
                <ResourceForm
                  fields={IMAGE_EDIT_FIELDS}
                  action={saveProjectImage.bind(null, id, item.id)}
                  values={{ alt_text: item.image.alt_text, display_order: item.display_order }}
                  submitLabel="Save image"
                />
                <DeleteButton action={deleteProjectImage.bind(null, id, item.id)} what="this image from the gallery" label="Remove" />
              </li>
            ))}
          </ul>
        )}
        <h3 className="mt-4 font-semibold">Add pictures</h3>
        {media.image.length === 0 ? (
          <p className="text-muted">No pictures in the library yet: upload them under Media first.</p>
        ) : (
          <GalleryPicker action={addProjectImages.bind(null, id, nextOrder)}>
            <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {media.image.map((choice) => {
                const added = inGallery.has(choice.id);
                return (
                  <li key={choice.id}>
                    <label
                      className={
                        added
                          ? "flex h-full flex-col gap-2 rounded-xl border border-line p-2 opacity-50"
                          : "flex h-full cursor-pointer flex-col gap-2 rounded-xl border border-line p-2 hover:border-paper has-checked:border-accent has-checked:bg-accent/10 has-focus-visible:outline-2 has-focus-visible:outline-accent"
                      }
                    >
                      <MediaImage
                        src={choice.url}
                        alt=""
                        width={choice.width}
                        height={choice.height}
                        sizes="(min-width: 1024px) 200px, 45vw"
                        loading="lazy"
                        className="aspect-[4/3] w-full rounded-lg bg-ink-raised object-contain"
                      />
                      <span className="flex items-start gap-2 text-xs">
                        <input type="checkbox" name="ids" value={choice.id} disabled={added} className="mt-0.5 accent-accent" />
                        <span className="break-all">{added ? `In the gallery · ${choice.label}` : choice.label}</span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </GalleryPicker>
        )}
      </section>
    </>
  );
}
