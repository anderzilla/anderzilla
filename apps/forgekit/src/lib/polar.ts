/**
 * Polar.sh integration helpers (stubs ready for live keys).
 *
 * TODO when you have Polar credentials:
 * 1. Create a product at https://polar.sh then copy Product ID into POLAR_PRODUCT_ID
 * 2. Create an organization access token then set POLAR_ACCESS_TOKEN
 * 3. Add a webhook endpoint pointing to /api/webhooks/polar then set POLAR_WEBHOOK_SECRET
 * 4. Uncomment the real fetch() calls below (search for TODO:POLAR)
 *
 * Docs: https://docs.polar.sh/api-reference/checkouts/create-session
 */

export type PolarCheckoutInput = {
  productId: string;
  successUrl: string;
  customerEmail?: string;
};

export type PolarCheckoutResult =
  | { ok: true; url: string; id: string; mode: "live" | "stub" }
  | { ok: false; error: string; mode: "stub" };

const POLAR_API_BASE = process.env.POLAR_API_BASE ?? "https://api.polar.sh/v1";

export function getPolarConfig() {
  return {
    accessToken: process.env.POLAR_ACCESS_TOKEN ?? "",
    webhookSecret: process.env.POLAR_WEBHOOK_SECRET ?? "",
    productId: process.env.POLAR_PRODUCT_ID ?? "",
    apiBase: POLAR_API_BASE,
    configured: Boolean(
      process.env.POLAR_ACCESS_TOKEN && process.env.POLAR_PRODUCT_ID
    ),
  };
}

/**
 * Creates a Polar checkout session.
 * Falls back to a documented stub when tokens are missing.
 */
export async function createCheckoutSession(
  input: PolarCheckoutInput
): Promise<PolarCheckoutResult> {
  const config = getPolarConfig();

  if (!config.accessToken || !input.productId) {
    return {
      ok: true,
      mode: "stub",
      id: `stub_checkout_${Date.now()}`,
      url: `${process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"}/dashboard?checkout=stub`,
    };
  }

  // TODO:POLAR — replace stub with live Polar Checkout Sessions API
  // const res = await fetch(`${config.apiBase}/checkouts/custom/`, {
  //   method: "POST",
  //   headers: {
  //     Authorization: `Bearer ${config.accessToken}`,
  //     "Content-Type": "application/json",
  //   },
  //   body: JSON.stringify({
  //     product_id: input.productId,
  //     success_url: input.successUrl,
  //     customer_email: input.customerEmail,
  //   }),
  // });
  // if (!res.ok) {
  //   const body = await res.text();
  //   return { ok: false, mode: "stub", error: `Polar error ${res.status}: ${body}` };
  // }
  // const data = (await res.json()) as { id: string; url: string };
  // return { ok: true, mode: "live", id: data.id, url: data.url };

  return {
    ok: true,
    mode: "stub",
    id: `stub_checkout_${Date.now()}`,
    url: input.successUrl,
  };
}

/**
 * Verify Polar webhook signature (HMAC).
 * TODO:POLAR — implement using POLAR_WEBHOOK_SECRET when live.
 */
export function verifyPolarWebhookSignature(
  _payload: string,
  _signatureHeader: string | null
): boolean {
  const secret = process.env.POLAR_WEBHOOK_SECRET;
  if (!secret) {
    console.warn("[polar] POLAR_WEBHOOK_SECRET missing — skipping signature verify (stub)");
    return true;
  }

  // TODO:POLAR — verify HMAC-SHA256 of raw body against Polar-Signature header
  console.warn("[polar] signature verify not implemented — accepting in stub mode");
  return true;
}
