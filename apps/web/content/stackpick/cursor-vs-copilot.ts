import type { StackPickComparison } from "./types";

export const cursorVsCopilot: StackPickComparison = {
  slug: "cursor-vs-copilot",
  title: "Cursor vs GitHub Copilot",
  category: "AI IDE",
  teaser: "AI-native editor vs the default GitHub-integrated assistant.",
  updated: "2026-09-08",
  author: "Anderzilla",
  productA: { id: "cursor-ai", name: "Cursor" },
  productB: { id: "github-copilot", name: "GitHub Copilot" },
  tldr:
    "Cursor wins if you want an AI-first IDE (chat, agentic edits, repo-aware workflows) and will pay for that focus. Copilot wins if you stay inside VS Code/JetBrains + GitHub and want the path of least friction. Note: Cursor’s public affiliate/referral program is closed — this page is editorial only.",
  verdictWinner: "a",
  verdictLabel: "Cursor for AI-native editing · Copilot for GitHub-native defaults",
  rows: [
    {
      feature: "Product shape",
      a: "Forked IDE built around AI",
      b: "Assistant layered on popular IDEs",
    },
    {
      feature: "Repo workflows",
      a: "Strong multi-file / agentic edits",
      b: "Excellent inline completions + chat",
    },
    {
      feature: "GitHub integration",
      a: "Works with GitHub; not GitHub-owned",
      b: "Deep GitHub ecosystem fit",
    },
    {
      feature: "Switching cost",
      a: "New editor habit",
      b: "Stay in your current IDE",
    },
    {
      feature: "Affiliate status (Anderzilla)",
      a: "closed — Cursor affiliate ended mid-2026",
      b: "STACKPICK_TODO — no publisher cash affiliate",
    },
  ],
  a: {
    pros: [
      "Feels purpose-built for AI pair programming",
      "Great for refactors across many files",
      "Fast iteration loop for indie builders",
    ],
    cons: [
      "Another editor to learn/maintain",
      "Affiliate program closed — no partner CTA here",
    ],
  },
  b: {
    pros: [
      "Lives where many already code",
      "Tight with GitHub PRs / enterprise rollouts",
      "Lower switching cost",
    ],
    cons: [
      "Less “AI IDE” identity than Cursor",
      "No public comparison-site affiliate to wire",
    ],
  },
  faq: [
    {
      q: "Why no “Buy via affiliate” button for Cursor?",
      a: "Cursor’s referral/affiliate program closed around mid-2026. We still publish the comparison because builders search it — we just don’t invent a commission link.",
    },
    {
      q: "Which should juniors start with?",
      a: "Copilot inside an editor you already know, unless you specifically want Cursor’s agent workflows. Tool skill ≠ fundamentals.",
    },
  ],
  notes: [
    "Cursor affiliate status: closed. Do not add sponsored Cursor links until a new official program exists.",
  ],
};
