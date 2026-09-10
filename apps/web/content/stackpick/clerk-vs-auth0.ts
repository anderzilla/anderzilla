import type { StackPickComparison } from "./types";

export const clerkVsAuth0: StackPickComparison = {
  slug: "clerk-vs-auth0",
  title: "Clerk vs Auth0",
  category: "Auth",
  teaser: "Modern React/Next auth UX vs enterprise identity platform gravity.",
  updated: "2026-09-08",
  author: "Anderzilla",
  productA: { id: "clerk", name: "Clerk" },
  productB: { id: "auth0", name: "Auth0" },
  tldr:
    "Clerk is the default pick for Next.js / React indie products that want beautiful prebuilt UI and fast time-to-login. Auth0 (Okta) wins when you need enterprise SSO catalogs, complex B2B identity, and procurement that already knows Auth0. Most Anderzilla-style indie apps → Clerk.",
  verdictWinner: "a",
  verdictLabel: "Clerk for indie Next.js · Auth0 for enterprise identity",
  rows: [
    {
      feature: "Best fit",
      a: "SaaS / indie apps on Next.js",
      b: "Enterprise & complex org SSO",
    },
    {
      feature: "UI components",
      a: "Excellent drop-in React components",
      b: "Universal Login + lots of config",
    },
    {
      feature: "DX",
      a: "Opinionated, fast",
      b: "Powerful, heavier",
    },
    {
      feature: "Pricing vibe",
      a: "MAU tiers friendly early",
      b: "Enterprise-leaning as you grow",
    },
    {
      feature: "Affiliate status (Anderzilla)",
      a: "STACKPICK_TODO — Creators partnership",
      b: "STACKPICK_TODO — no publisher cash affiliate",
    },
  ],
  a: {
    pros: [
      "Best-in-class Next.js integration feel",
      "Prebuilt UIs that don’t look like 2014",
      "Organizations / B2B features improving fast",
    ],
    cons: [
      "Lock-in if you lean hard on their components",
      "Commission model for publishers not a classic % link yet",
    ],
  },
  b: {
    pros: [
      "Deep enterprise protocol / SSO coverage",
      "Known quantity for security teams",
      "Huge ecosystem of guides",
    ],
    cons: [
      "Heavier for a weekend MVP",
      "Pricing and packaging can feel enterprise-first",
    ],
  },
  faq: [
    {
      q: "Should I roll my own auth instead?",
      a: "Only if auth is your product. For ForgeKit-style apps, managed auth usually ships faster and safer.",
    },
    {
      q: "Why are CTAs placeholders?",
      a: "No invented partnerships. Clerk Creators and Auth0 partner paths need approval before live affiliate/sponsored links.",
    },
  ],
};
