import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession, isDemoMode } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LogoutButton } from "@/components/logout-button";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ checkout?: string; purchased?: string }>;
}) {
  const session = await getSession();
  if (!session) {
    redirect("/login");
  }

  const params = await searchParams;

  let entitlements: { id: string; productId: string; status: string; source: string }[] = [];
  if (!session.demo) {
    try {
      entitlements = await prisma.entitlement.findMany({
        where: { userId: session.userId },
        select: { id: true, productId: true, status: true, source: true },
        orderBy: { createdAt: "desc" },
        take: 10,
      });
    } catch {
      entitlements = [];
    }
  }

  const gatedUnlocked = session.demo || entitlements.some((e) => e.status === "active");

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-300">
            ← ForgeKit
          </Link>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-zinc-400">
            Signed in as {session.email}
            {session.demo ? " (demo mode)" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isDemoMode() ? <LogoutButton /> : null}
          <Link href="/">
            <Button variant="secondary" size="sm">
              Marketing site
            </Button>
          </Link>
        </div>
      </header>

      {params.checkout === "stub" || params.purchased === "1" ? (
        <Card className="mb-6 border-amber-500/30">
          <p className="text-sm text-amber-200">
            Checkout stub completed. Wire Polar live keys to replace this demo redirect.
          </p>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h2 className="font-medium text-zinc-100">Gated feature</h2>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            Example premium surface. Unlocked in DEMO_MODE or when the user has an active
            Entitlement row.
          </p>
          {gatedUnlocked ? (
            <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200">
              Unlocked — export sample, API keys panel, or your real product feature goes here.
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-zinc-700 bg-zinc-950 p-4 text-sm text-zinc-400">
              Locked — purchase ForgeKit or grant an entitlement via the Polar webhook.
            </div>
          )}
        </Card>

        <Card>
          <h2 className="font-medium text-zinc-100">Entitlements</h2>
          {session.demo ? (
            <p className="mt-2 text-sm text-zinc-400">
              Demo mode skips the database. Set DEMO_MODE=false and run the db:push script
              for real entitlement rows.
            </p>
          ) : entitlements.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-400">No entitlements yet.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-zinc-300">
              {entitlements.map((e) => (
                <li key={e.id} className="rounded-lg border border-zinc-800 px-3 py-2">
                  {e.productId} · {e.status} · {e.source}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
