import type { Field } from "@/lib/admin/fields";

export const CERTIFICATIONS_FIELDS: readonly Field[] = [
  { kind: "text", name: "name", label: "Name", required: true, maxLength: 200 },
  { kind: "text", name: "issuing_organization", label: "Issuing organization", required: true, maxLength: 200 },
  { kind: "text", name: "credential_id", label: "Credential ID", maxLength: 150 },
  { kind: "text", name: "credential_url", label: "Credential URL", inputType: "url", maxLength: 2048 },
  { kind: "date", name: "issued_at", label: "Issued" },
  { kind: "date", name: "expires_at", label: "Expires", hint: "Empty: doesn't expire." },
  {
    kind: "media",
    name: "image_media_id",
    label: "Certificate picture",
    mediaKind: "image",
    upload: true,
    hint: 'Pick one from the media library or upload a new one. Visitors open it with "View certificate".',
  },
];
