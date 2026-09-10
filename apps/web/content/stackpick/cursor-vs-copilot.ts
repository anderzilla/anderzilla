import type { StackPickComparison } from "./types";

export const cursorVsCopilot: StackPickComparison = {
  slug: "cursor-vs-copilot",
  title: "Cursor vs GitHub Copilot",
  category: "AI IDE",
  teaser: "AI-native editor vs the default GitHub-integrated assistant.",
  updated: "2026-09-08",
  author: "AnderZilla",
  productA: { id: "cursor-ai", name: "Cursor" },
  productB: { id: "github-copilot", name: "GitHub Copilot" },
  tldr:
    "Cursor wins if you want an AI-first IDE (chat, agentic edits, repo-aware workflows) and will pay for that focus. Copilot wins if you stay inside VS Code/JetBrains + GitHub and want the path of least friction.",
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
  ],
  a: {
    pros: [
      "Feels purpose-built for AI pair programming",
      "Great for refactors across many files",
      "Fast iteration loop for indie builders",
    ],
    cons: [
      "Another editor to learn/maintain",
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
    ],
  },
  faq: [
    {
      q: "Which should juniors start with?",
      a: "Copilot inside an editor you already know, unless you specifically want Cursor’s agent workflows. Tool skill ≠ fundamentals.",
    },
  ],
  notes: [
  ],
};
