/**
 * Affiliate / partner link registry for StackPick and future hubs.
 * Do NOT invent live partnerships — keep TODO placeholders until real programs are approved.
 */

export type AffiliateSlot = {
  id: string;
  label: string;
  category: "ai" | "devtools" | "hosting" | "gpu" | "auth" | "database" | "gear" | "other";
  /** Official product / docs URL (non-affiliate, safe to link for reading) */
  productUrl?: string | null;
  /** Placeholder until a real affiliate URL is approved */
  href: string | null;
  status: "STACKPICK_TODO" | "live" | "closed";
  notes?: string;
};

export const AFFILIATE_DISCLOSURE =
  "Some links on Anderzilla and StackPick may be affiliate links. If you buy through them, I may earn a commission at no extra cost to you. I only recommend tools I'd use myself.";

export const STACKPICK_AFFILIATES: AffiliateSlot[] = [
  {
    id: "railway",
    label: "Railway",
    category: "hosting",
    productUrl: "https://railway.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "1P affiliate exists — wire referral URL after signup.",
  },
  {
    id: "render",
    label: "Render",
    category: "hosting",
    productUrl: "https://render.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "No verified public cash affiliate for publishers.",
  },
  {
    id: "vast-ai",
    label: "Vast.ai",
    category: "gpu",
    productUrl: "https://vast.ai",
    href: null,
    status: "STACKPICK_TODO",
    notes: "1P referral — use dashboard link when ready.",
  },
  {
    id: "runpod",
    label: "RunPod",
    category: "gpu",
    productUrl: "https://www.runpod.io",
    href: null,
    status: "STACKPICK_TODO",
    notes: "Referral first; PartnerStack cash after gate.",
  },
  {
    id: "clerk",
    label: "Clerk",
    category: "auth",
    productUrl: "https://clerk.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "Creators partnership — not classic % affiliate yet.",
  },
  {
    id: "auth0",
    label: "Auth0",
    category: "auth",
    productUrl: "https://auth0.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "Okta Elevate B2B — no publisher cash affiliate.",
  },
  {
    id: "neon",
    label: "Neon",
    category: "database",
    productUrl: "https://neon.tech",
    href: null,
    status: "STACKPICK_TODO",
    notes: "OSS/platform partners — not general blog affiliate.",
  },
  {
    id: "supabase",
    label: "Supabase",
    category: "database",
    productUrl: "https://supabase.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "Partner form — commission not confirmed publicly.",
  },
  {
    id: "cursor-ai",
    label: "Cursor (AI IDE)",
    category: "ai",
    productUrl: "https://cursor.com",
    href: null,
    status: "closed",
    notes: "Cursor affiliate/referral closed (mid-2026). Comparison content only.",
  },
  {
    id: "github-copilot",
    label: "GitHub Copilot",
    category: "ai",
    productUrl: "https://github.com/features/copilot",
    href: null,
    status: "STACKPICK_TODO",
    notes: "No public publisher cash affiliate.",
  },
  {
    id: "vercel",
    label: "Vercel",
    category: "hosting",
    productUrl: "https://vercel.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "Official Dub affiliate is v0-focused, not all hosting.",
  },
  {
    id: "netlify",
    label: "Netlify",
    category: "hosting",
    productUrl: "https://www.netlify.com",
    href: null,
    status: "STACKPICK_TODO",
    notes: "PartnerStack — apply before linking.",
  },
  {
    id: "openai-api",
    label: "OpenAI API",
    category: "ai",
    productUrl: "https://platform.openai.com",
    href: null,
    status: "STACKPICK_TODO",
  },
  {
    id: "anthropic",
    label: "Anthropic Claude",
    category: "ai",
    productUrl: "https://www.anthropic.com",
    href: null,
    status: "STACKPICK_TODO",
  },
  {
    id: "cloudflare",
    label: "Cloudflare",
    category: "hosting",
    productUrl: "https://www.cloudflare.com",
    href: null,
    status: "STACKPICK_TODO",
  },
];

export function getAffiliate(id: string): AffiliateSlot | undefined {
  return STACKPICK_AFFILIATES.find((a) => a.id === id);
}

export const SITE = {
  name: "AnderZilla",
  domain: "anderzilla.com",
  url: "https://anderzilla.com",
  tagline: "Tools, stacks & geek fuel for builders who ship.",
  author: "Anderson Henrique Gonçalves",
  authorShort: "AnderZilla",
  location: "Curitiba, Brazil · Remote",
  role: "Senior Software Engineer / Architect",
  email: "hello@anderzilla.com",
  forgekit: {
    name: "ForgeKit",
    price: "US$149",
    gumroad: "https://anderzilla.gumroad.com/l/edkel",
    demo: "https://forgekit-kwzn5potra-rj.a.run.app",
    blurb:
      "A serious Next.js MVP kit — landing, auth, Prisma entitlements, gated dashboard, and checkout-ready architecture. Gumroad ZIP delivery.",
  },
  social: {
    github: "https://github.com/anderzilla",
    twitter: "https://x.com/anderzilla",
    linkedin: "https://www.linkedin.com/in/andersonhenriquegoncalves",
  },
  future: [
    {
      id: "gear31",
      name: "Gear31.club",
      blurb: "Curated gear for builders & gamers. Coming soon.",
    },
    {
      id: "newsletter",
      name: "Anderzilla Weekly",
      blurb: "Ship notes, stack picks, and geek culture — no fluff.",
    },
  ],
} as const;
