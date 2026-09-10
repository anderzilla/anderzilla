import { NextRequest, NextResponse } from "next/server";
import { verifyPolarWebhookSignature } from "@/lib/polar";
import { prisma } from "@/lib/prisma";

/**
 * POST /api/webhooks/polar
 * Polar webhook handler stub. Logs events and grants entitlements when possible.
 * Configure URL: https://YOUR_DOMAIN/api/webhooks/polar
 * TODO:POLAR — map live Polar event field paths.
 */
export async function POST(req: NextRequest) {
  const raw = await req.text();
  const signature =
    req.headers.get("polar-signature") ??
    req.headers.get("webhook-signature") ??
    req.headers.get("x-polar-signature");

  if (!verifyPolarWebhookSignature(raw, signature)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  let event: { type?: string; data?: Record<string, unknown> };
  try {
    event = JSON.parse(raw) as { type?: string; data?: Record<string, unknown> };
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  console.log("[polar webhook]", event.type ?? "unknown", JSON.stringify(event.data ?? {}));

  try {
    const data = event.data ?? {};
    const email =
      (data.customer_email as string | undefined) ??
      ((data.customer as { email?: string } | undefined)?.email);
    const productId =
      (data.product_id as string | undefined) ??
      process.env.POLAR_PRODUCT_ID ??
      "unknown";
    const orderId = (data.id as string | undefined) ?? undefined;

    if (email && event.type?.includes("order")) {
      const user = await prisma.user.upsert({
        where: { email },
        create: { email },
        update: {},
      });
      await prisma.entitlement.create({
        data: {
          userId: user.id,
          productId,
          status: "active",
          source: "polar",
          polarOrderId: orderId,
        },
      });
      console.log("[polar webhook] entitlement granted for", email);
    }
  } catch (err) {
    console.warn("[polar webhook] entitlement stub skipped:", err);
  }

  return NextResponse.json({ received: true });
}
