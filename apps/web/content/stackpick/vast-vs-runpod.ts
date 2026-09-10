import type { StackPickComparison } from "./types";

export const vastVsRunpod: StackPickComparison = {
  slug: "vast-vs-runpod",
  title: "Vast.ai vs RunPod",
  category: "GPU cloud",
  teaser: "Rent GPUs for training and inference without a hyperscaler bill.",
  updated: "2026-09-08",
  author: "AnderZilla",
  productA: { id: "vast-ai", name: "Vast.ai" },
  productB: { id: "runpod", name: "RunPod" },
  tldr:
    "Vast.ai wins when you hunt lowest $/hour across a marketplace of hosts. RunPod wins when you want a cleaner product UX for pods + serverless-style GPU jobs. Power users shopping spot GPUs → Vast; builders who want less marketplace friction → RunPod.",
  verdictWinner: "tie",
  verdictLabel: "Vast for raw $/GPU · RunPod for smoother product UX",
  rows: [
    {
      feature: "Model",
      a: "Marketplace of GPU hosts",
      b: "Managed pods + serverless GPU",
    },
    {
      feature: "Price sensitivity",
      a: "Often cheapest if you shop carefully",
      b: "Competitive; more packaged offers",
    },
    {
      feature: "Reliability feel",
      a: "Varies by host — vet listings",
      b: "More uniform platform experience",
    },
    {
      feature: "Serverless / endpoints",
      a: "More DIY around instances",
      b: "Stronger serverless story",
    },
  ],
  a: {
    pros: [
      "Aggressive pricing when you filter well",
      "Huge variety of GPU SKUs",
    ],
    cons: [
      "Marketplace quality variance",
      "More homework before trusting a host",
    ],
  },
  b: {
    pros: [
      "Cleaner pod UX for many ML builders",
      "Serverless options reduce ops toil",
    ],
    cons: [
      "May cost more than the absolute cheapest Vast listing",
    ],
  },
  faq: [
    {
      q: "Which for fine-tuning a 7B model?",
      a: "Either works. Start with a short rented A100/H100-class pod, measure tokens/sec and $/hour, then lock a provider. Don’t pre-commit annual spend.",
    },
    {
      q: "Is this financial advice?",
      a: "No — GPU markets move weekly. Treat this as a decision framework, not a permanent ranking.",
    },
  ],
};
