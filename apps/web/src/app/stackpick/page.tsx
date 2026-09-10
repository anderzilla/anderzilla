import type { Metadata } from "next";
import Link from "next/link";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE, STACKPICK_AFFILIATES } from "../../../content/affiliates";
import { listComparisons } from "../../../content/stackpick";

export const metadata: Metadata = {
  title: "StackPick",
  description:
    "StackPick — Wirecutter-lite comparisons for AI, hosting, auth, databases, and GPU cloud. Affiliate slots stay placeholders until partnerships are live.",
  openGraph: {
    title: `StackPick · ${SITE.name}`,
    description: "Honest AI/dev comparisons. No invented partnerships.",
    url: `${SITE.url}/stackpick`,
  },
};

export default function StackPickPage() {
  const comparisons = listComparisons();

  return (
    <div className="container-page py-16">
      <p className="badge">pSEO · Wirecutter-lite</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        StackPick
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-zinc-300">
        Side-by-side picks for builders who want tradeoffs, not hype decks. Written by{" "}
        {SITE.authorShort} — personal brand, not a faceless review farm.
      </p>

      <AffiliateDisclosure className="mt-8" />

      <section className="mt-12">
        <h2 className="section-title">Comparisons</h2>
        <p className="mt-2 muted text-sm">
          Each page: TL;DR · table · pros/cons · FAQ · CTA placeholders from{" "}
          <code className="font-mono text-violet-soft">content/affiliates.ts</code>.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {comparisons.map((c) => (
            <Link
              key={c.slug}
              href={`/stackpick/${c.slug}`}
              className="card flex flex-col transition hover:border-violet-soft/40"
            >
              <span className="badge w-fit">{c.category}</span>
              <h3 className="mt-3 font-semibold text-white">{c.title}</h3>
              <p className="mt-2 flex-1 text-sm text-zinc-400">{c.teaser}</p>
              <p className="mt-4 font-mono text-xs text-zinc-500">
                Updated {c.updated} · {c.author}
              </p>
              <span className="mt-3 text-sm font-medium text-amber-soft">
                Read comparison →
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="section-title">Affiliate slots</h2>
        <p className="mt-2 muted text-sm">
          Status{" "}
          <span className="font-mono text-amber-soft">STACKPICK_TODO</span> /{" "}
          <span className="font-mono text-amber-soft">closed</span> until live.
        </p>
        <div className="mt-6 overflow-hidden rounded-2xl border border-ink-600">
          <table className="w-full text-left text-sm">
            <thead className="bg-ink-800 text-zinc-300">
              <tr>
                <th className="px-4 py-3 font-medium">Tool</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {STACKPICK_AFFILIATES.map((a) => (
                <tr key={a.id} className="border-t border-ink-600/80">
                  <td className="px-4 py-3 text-zinc-200">{a.label}</td>
                  <td className="px-4 py-3 text-zinc-400">{a.category}</td>
                  <td className="px-4 py-3 font-mono text-xs text-amber-soft">
                    {a.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="mt-10 text-sm text-zinc-500">
        Looking for the product kit instead?{" "}
        <Link href="/forgekit" className="text-amber-soft hover:underline">
          ForgeKit
        </Link>
      </p>
    </div>
  );
}
