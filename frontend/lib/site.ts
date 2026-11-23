/** Site-wide text and navigation. Profile data (name, headline, links) comes from the API from F4. */
export const SITE = {
  name: "Devin Bendaño",
  // The production address: canonical links, the sitemap and Open Graph URLs are built on it,
  // so search engines index this domain and never a preview or *.vercel.app address.
  url: "https://bendanodevinp.online",
  // The home page's title and description, also the defaults for Open Graph. Sized for search
  // results (lib/site.test.ts): a title of 50-60 characters and a description of 120-160 are
  // shown whole, and both name the role and stack people search for.
  title: "Devin Bendaño | Full-Stack Developer, FastAPI & Next.js",
  description:
    "Portfolio of Devin Bendaño, a full-stack developer in the Philippines building APIs, backend systems and web applications. Projects, writing and experience.",
} as const;

export const NAV_ITEMS = [
  { href: "/projects", label: "Projects" },
  { href: "/about", label: "About" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
] as const;
