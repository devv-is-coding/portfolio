/** Site-wide text and navigation. Profile data (name, headline, links) comes from the API from F4. */
export const SITE = {
  name: "Devin Bendaño",
  // The production address: canonical links, the sitemap and Open Graph URLs are built on it,
  // so search engines index this domain and never a preview or *.vercel.app address.
  url: "https://bendanodevinp.online",
  title: "Devin Bendaño: developer portfolio",
  description: "Projects, writing and experience of Devin Bendaño, a full-stack developer.",
} as const;

export const NAV_ITEMS = [
  { href: "/projects", label: "Projects" },
  { href: "/about", label: "About" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
] as const;
