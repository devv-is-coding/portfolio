// How the platforms spell their own names. The admin stores whatever was typed ("linkedin").
const PLATFORM_NAMES: Readonly<Record<string, string>> = {
  behance: "Behance",
  devto: "DEV",
  "dev.to": "DEV",
  discord: "Discord",
  dribbble: "Dribbble",
  facebook: "Facebook",
  github: "GitHub",
  gitlab: "GitLab",
  instagram: "Instagram",
  linkedin: "LinkedIn",
  medium: "Medium",
  stackoverflow: "Stack Overflow",
  "stack overflow": "Stack Overflow",
  telegram: "Telegram",
  tiktok: "TikTok",
  twitter: "X",
  upwork: "Upwork",
  whatsapp: "WhatsApp",
  x: "X",
  youtube: "YouTube",
};

/** A social link's platform as visitors expect to read it: "linkedin" -> "LinkedIn". */
export function platformName(platform: string): string {
  const typed = platform.trim();
  const known = PLATFORM_NAMES[typed.toLowerCase()];
  if (known) {
    return known;
  }
  // Unknown names keep any capitals they were typed with; all-lowercase ones get a capital.
  return typed === typed.toLowerCase() ? typed.charAt(0).toUpperCase() + typed.slice(1) : typed;
}
