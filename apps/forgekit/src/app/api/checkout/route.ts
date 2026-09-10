import { NextRequest, NextResponse } from "next/server";
import { createCheckoutSession, getPolarConfig } from "@/lib/polar";

/**
 * POST /api/checkout
 *
 * Starts a Polar checkout for ForgeKit (US$149 one-time).
 * Without Polar env vars, returns a stub URL so local demos still work.
 *
 * How to wire live Polar:
 * 1. Set POLAR_ACCESS_TOKEN, POLAR_PRODUCT_ID in .env
 * 2. Implement the fetch in src/lib/polar.ts (TODO:POLAR)
 * 3. Point Polar success_url to /dashboard?purchased=1
 */
export async function POST(req: NextRequest) {
  const config = getPolarConfig();
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

  let email: string | undefined;
  try {
    const body = (await req.json()) as { email?: string };
    email = body.email;
  } catch {
    // empty body is fine
  }

  const productId = config.productId || "missing-product-id";

  const result = await createCheckoutSession({
    productId,
    successUrl: `${appUrl}/dashboard?purchased=1`,
    customerEmail: email,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({
    url: result.url,
    id: result.id,
    mode: result.mode,
    configured: config.configured,
    message:
      result.mode === "stub"
        ? "Polar keys not fully wired — returning stub checkout URL. See README and src/lib/polar.ts."
        : "Checkout session created",
  });
}

export async function GET() {
  const config = getPolarConfig();
  return NextResponse.json({
    endpoint: "/api/checkout",
    method: "POST",
    configured: config.configured,
    productIdSet: Boolean(config.productId),
    docs: "POST JSON { email?: string } → { url, id, mode }. Redirect the buyer to url.",
  });
}
