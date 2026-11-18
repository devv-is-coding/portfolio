import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { EmptyState } from "@/components/ui/empty-state";
import { Tag } from "@/components/ui/tag";
import { asAdmin } from "@/lib/auth/session";
import { deleteSetting, saveSetting } from "./_lib/actions";
import { SETTING_EDIT_FIELDS, SETTING_NEW_FIELDS } from "./_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Settings" };

export default async function SettingsPage() {
  const { items } = await asAdmin((api) => api.GET("/admin/settings", { params: { query: { size: 100 } } }));

  return (
    <>
      <PageHeader eyebrow="Site" title="Settings" />
      <div className="flex flex-col gap-6">
        {items.length === 0 && <EmptyState title="No settings yet" />}
        {items.map((setting) => (
          <article key={setting.key} className="flex flex-col gap-4 rounded-2xl border border-line p-5">
            <h2 className="flex flex-wrap items-center gap-3 font-mono text-sm">
              {setting.key}
              <Tag className={setting.is_public ? "border-accent text-accent" : undefined}>
                {setting.is_public ? "Public" : "Private"}
              </Tag>
            </h2>
            <ResourceForm
              fields={SETTING_EDIT_FIELDS}
              action={saveSetting.bind(null, setting.key)}
              values={{ value: JSON.stringify(setting.value, null, 2) }}
              submitLabel="Save"
            />
            <DeleteButton action={deleteSetting.bind(null, setting.key)} what={`the setting ${setting.key}`} />
          </article>
        ))}
      </div>
      <section className="mt-16 flex flex-col gap-6 border-t border-line pt-10" aria-labelledby="new-setting">
        <h2 id="new-setting" className="font-display text-2xl font-extrabold">
          New setting
        </h2>
        <ResourceForm fields={SETTING_NEW_FIELDS} action={saveSetting.bind(null, null)} submitLabel="Add setting" />
      </section>
    </>
  );
}
