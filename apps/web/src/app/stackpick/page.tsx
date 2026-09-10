import type { Metadata } from "next";
import Link from "next/link";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE } from "../../../content/affiliates";
import { listComparisons } from "../../../content/stackpick";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/stackpick` },
  title: "StackPick",
  description:
    "Compare developer tools across hosting, AI, authentication, databases, and GPU cloud. Explore use cases, tradeoffs, and official product links.",
  openGraph: {
    title: `StackPick · ${SITE.name}`,
    description: "Developer tool comparisons organized around your use case.",
    url: `${SITE.url}/stackpick`,
  },
};

export default function StackPickPage() {
  const comparisons = listComparisons();

  return (
    <div className="container-page py-16">
      <p className="badge">Developer tool comparisons</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        StackPick
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-zinc-300">
        Side-by-side perspectives on the tools behind your next project. Written
        by {SITE.authorShort}.
      </p>

      <AffiliateDisclosure className="mt-8" />

      <section className="mt-12">
        <h2 className="section-title">Comparisons</h2>
        <p className="mt-2 muted text-sm">
          Start with the verdict, compare key differences, and review the pros,
          cons, and FAQs.
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

      <section className="mt-14 card">
        <h2 className="section-title">How to use these comparisons</h2>
        <p className="mt-3 max-w-3xl leading-relaxed text-zinc-400">
          These are editorial starting points, not benchmark results. Choose the
          tradeoffs that fit your workload, budget, and team. Visit the official
          product sites for current features, limits, and pricing before making
          a decision.
        </p>
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
