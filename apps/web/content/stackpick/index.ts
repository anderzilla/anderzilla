import type { StackPickComparison } from "./types";
import { clerkVsAuth0 } from "./clerk-vs-auth0";
import { cursorVsCopilot } from "./cursor-vs-copilot";
import { neonVsSupabase } from "./neon-vs-supabase";
import { railwayVsRender } from "./railway-vs-render";
import { vastVsRunpod } from "./vast-vs-runpod";

export const STACKPICK_COMPARISONS: StackPickComparison[] = [
  railwayVsRender,
  vastVsRunpod,
  clerkVsAuth0,
  neonVsSupabase,
  cursorVsCopilot,
];

export function getComparison(slug: string): StackPickComparison | undefined {
  return STACKPICK_COMPARISONS.find((c) => c.slug === slug);
}

export function listComparisons(): StackPickComparison[] {
  return STACKPICK_COMPARISONS;
}

export type { StackPickComparison } from "./types";
