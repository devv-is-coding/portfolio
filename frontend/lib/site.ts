/** Site-wide text and navigation. Profile data (name, headline, links) comes from the API from F4. */
export const SITE = {
  name: "Devin Bendaño",
  title: "Devin Bendaño: developer portfolio",
  description: "Projects, writing and experience of Devin Bendaño, a full-stack developer.",
} as const;

export const NAV_ITEMS = [
  { href: "/projects", label: "Projects" },
  { href: "/about", label: "About" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
] as const;
