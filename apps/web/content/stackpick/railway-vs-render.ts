import type { StackPickComparison } from "./types";

export const railwayVsRender: StackPickComparison = {
  slug: "railway-vs-render",
  title: "Railway vs Render",
  category: "Hosting",
  teaser: "PaaS for indie backends — DX, pricing surprises, and when to pick each.",
  updated: "2026-09-08",
  author: "Anderzilla",
  productA: { id: "railway", name: "Railway" },
  productB: { id: "render", name: "Render" },
  tldr:
    "Pick Railway when you want fast deploys, flexible services, and usage-based billing you can watch closely. Pick Render when you want a clearer free/hobby path and more “classic PaaS” mental model. For most solo builders shipping APIs + workers, Railway wins on velocity; Render wins on predictability.",
  verdictWinner: "a",
  verdictLabel: "Railway for shipping velocity · Render for predictable hobby plans",
  rows: [
    {
      feature: "Best for",
      a: "Indie backends, workers, multi-service apps",
      b: "Web services + cron with simpler plan tiers",
    },
    {
      feature: "Billing model",
      a: "Usage-based (watch metrics)",
      b: "Plan tiers + instance sizes",
    },
    {
      feature: "DX / deploys",
      a: "Excellent CLI + dashboard loop",
      b: "Solid Git-connected deploys",
    },
    {
      feature: "Databases",
      a: "First-party Postgres plugins",
      b: "Managed Postgres / Redis add-ons",
    },
    {
      feature: "Free / hobby",
      a: "Credits / trial style — verify current offer",
      b: "Hobby free tier historically friendlier",
    },
    {
      feature: "Affiliate status (Anderzilla)",
      a: "STACKPICK_TODO — 1P program exists",
      b: "STACKPICK_TODO — no verified publisher affiliate",
    },
  ],
  a: {
    pros: [
      "Fast path from repo → running service",
      "Good fit for multi-service indie stacks",
      "Active product surface for builders",
    ],
    cons: [
      "Usage bills can surprise if you ignore metrics",
      "Need discipline on sleep/scale settings",
    ],
  },
  b: {
    pros: [
      "Familiar PaaS shapes (web, worker, cron)",
      "Often clearer hobby/free expectations",
      "Fine default for simple Node/Python APIs",
    ],
    cons: [
      "Less “playground” feel for complex topologies",
      "No verified cash affiliate for this publisher yet",
    ],
  },
  faq: [
    {
      q: "Which is cheaper for a side project?",
      a: "It depends on idle time and traffic. Render’s hobby framing is often easier to budget; Railway can be cheaper or pricier depending on how hard you run services. Check both calculators with your expected CPU/RAM hours.",
    },
    {
      q: "Can I run Docker on both?",
      a: "Yes — both support container-style deploys. Prefer the one whose dashboard you actually open weekly.",
    },
    {
      q: "Are the CTAs affiliate links?",
      a: "Not yet. Buttons below use STACKPICK_TODO placeholders until programs are approved and wired in content/affiliates.ts.",
    },
  ],
  notes: [
    "Prices and free tiers change — re-check official pricing before committing production spend.",
  ],
};
