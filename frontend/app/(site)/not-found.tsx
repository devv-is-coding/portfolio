import type { Metadata } from "next";
import { NotFoundMessage } from "@/components/not-found-message";

export const metadata: Metadata = {
  title: "Page not found",
};

// notFound() inside a site page (a project or post that doesn't exist) lands here, inside the
// (site) layout, which already has the header and footer. Without it the root not-found page
// rendered there too: two headers, two footers, and two elements with the header's view
// transition name, which aborts page transitions.
export default function SiteNotFound() {
  return <NotFoundMessage />;
}
