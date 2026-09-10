import type { StackPickComparison } from "./types";

export const neonVsSupabase: StackPickComparison = {
  slug: "neon-vs-supabase",
  title: "Neon vs Supabase",
  category: "Database",
  teaser: "Serverless Postgres vs Postgres-plus-backend platform.",
  updated: "2026-09-08",
  author: "Anderzilla",
  productA: { id: "neon", name: "Neon" },
  productB: { id: "supabase", name: "Supabase" },
  tldr:
    "Choose Neon when you want excellent serverless Postgres (branching, scale-to-zero) and you’ll bring your own auth/storage/API. Choose Supabase when you want Postgres + auth + storage + realtime as one platform. Pure DB craft → Neon; full BaaS velocity → Supabase.",
  verdictWinner: "tie",
  verdictLabel: "Neon for Postgres craft · Supabase for full-stack backend kit",
  rows: [
    {
      feature: "Core offer",
      a: "Serverless Postgres",
      b: "Postgres + auth + storage + realtime",
    },
    {
      feature: "Branching / previews",
      a: "Excellent DB branching story",
      b: "Strong platform; DB branching less central",
    },
    {
      feature: "Auth / storage",
      a: "Bring your own",
      b: "Included first-party",
    },
    {
      feature: "SQL comfort",
      a: "Pure Postgres focus",
      b: "Postgres + platform APIs",
    },
    {
      feature: "Affiliate status (Anderzilla)",
      a: "STACKPICK_TODO — OSS/platform partners",
      b: "STACKPICK_TODO — partner form",
    },
  ],
  a: {
    pros: [
      "Delightful for preview environments",
      "Scale-to-zero friendly for side projects",
      "Feels like “Postgres done right” for serverless",
    ],
    cons: [
      "You still assemble auth/files/etc.",
      "Not a classic comparison-blog affiliate today",
    ],
  },
  b: {
    pros: [
      "One dashboard for most MVP backend needs",
      "Great docs and community examples",
      "Realtime and storage save weeks",
    ],
    cons: [
      "Platform surface area = more opinions",
      "Public publisher commission not confirmed — placeholders only",
    ],
  },
  faq: [
    {
      q: "Can I use Prisma / Drizzle with both?",
      a: "Yes. Both are Postgres. Prefer the provider whose ops model matches your deploy story.",
    },
    {
      q: "What about Firebase?",
      a: "Different model (document + Google ecosystem). Google Cloud affiliate programs also have geo limits — not assumed here.",
    },
  ],
};
