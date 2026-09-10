"use client";

import { Button } from "@/components/ui/button";

const GUMROAD_URL =
  process.env.NEXT_PUBLIC_GUMROAD_URL ?? "https://anderzilla.gumroad.com/l/edkel";

/**
 * Primary buy CTA → Gumroad.
 * In-app /api/checkout remains available for optional MoR experiments in the source kit.
 */
export function BuyButton({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <a href={GUMROAD_URL} target="_blank" rel="noopener noreferrer">
        <Button type="button" size="lg" className="w-full">
          Buy on Gumroad — US$149
        </Button>
      </a>
      <p className="max-w-xs text-xs text-zinc-400">
        Secure checkout on Gumroad. Instant ZIP download + GETTING_STARTED.md after purchase.
      </p>
    </div>
  );
}
