import Link from "next/link";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { getAffiliate, SITE } from "../../content/affiliates";
import type { StackPickComparison as Comparison } from "../../content/stackpick/types";

function CtaButton({
  affiliateId,
  productName,
}: {
  affiliateId: string;
  productName: string;
}) {
  const slot = getAffiliate(affiliateId);
  const status = slot?.status ?? "STACKPICK_TODO";
  const href = slot?.href;
  const productUrl = slot?.productUrl ?? null;

  if (status === "live" && href) {
    return (
      <a
        href={href}
        className="btn-primary"
        target="_blank"
        rel="sponsored noopener noreferrer"
      >
        Check {productName}
      </a>
    );
  }

  if (productUrl) {
    return (
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <a
          href={productUrl}
          className="btn-secondary"
          target="_blank"
          rel="noopener noreferrer"
        >
          Visit {productName} (official)
        </a>
      </div>
    );
  }

  return (
    <span className="text-sm text-zinc-400">
      Official link unavailable for {productName}.
    </span>
  );
}

export function StackPickComparisonView({ data }: { data: Comparison }) {
  const winnerName =
    data.verdictWinner === "a"
      ? data.productA.name
      : data.verdictWinner === "b"
        ? data.productB.name
        : "Split decision";

  return (
    <article className="container-page py-16">
      <nav aria-label="Breadcrumb" className="text-sm text-zinc-500">
        <Link href="/stackpick" className="hover:text-amber-soft">
          StackPick
        </Link>
        <span className="mx-2">/</span>
        <span className="text-zinc-400">{data.title}</span>
      </nav>

      <p className="badge mt-6">{data.category}</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        {data.title}
      </h1>
      <p className="mt-3 max-w-2xl text-lg text-zinc-300">{data.teaser}</p>
      <p className="mt-3 font-mono text-xs text-zinc-500">
        By {data.author} · Updated {data.updated}
      </p>

      <AffiliateDisclosure className="mt-8" />

      <section className="mt-10 card border-amber-glow/25 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-soft">
          TL;DR verdict
        </p>
        <p className="mt-2 text-xl font-semibold text-white">
          {data.verdictLabel}
        </p>
        <p className="mt-3 text-zinc-300 leading-relaxed">{data.tldr}</p>
        <p className="mt-4 font-mono text-sm text-violet-soft">
          Best fit: {winnerName}
        </p>
      </section>

      <section className="mt-12">
        <h2 className="section-title">Comparison table</h2>
        <div className="mt-6 overflow-x-auto rounded-2xl border border-ink-600">
          <table className="w-full min-w-[640px] text-left text-sm">
            <caption className="sr-only">{data.title}: key differences</caption>
            <thead className="bg-ink-800 text-zinc-300">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">
                  Dimension
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  {data.productA.name}
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  {data.productB.name}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr
                  key={row.feature}
                  className="border-t border-ink-600/80 align-top"
                >
                  <td className="px-4 py-3 font-medium text-zinc-200">
                    {row.feature}
                  </td>
                  <td className="px-4 py-3 text-zinc-400">{row.a}</td>
                  <td className="px-4 py-3 text-zinc-400">{row.b}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-12 grid gap-4 md:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-white">
            {data.productA.name} — pros & cons
          </h2>
          <ul className="mt-4 space-y-2 text-sm text-zinc-300">
            {data.a.pros.map((p) => (
              <li key={p} className="flex gap-2">
                <span className="text-amber-soft">+</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
          <ul className="mt-4 space-y-2 text-sm text-zinc-400">
            {data.a.cons.map((c) => (
              <li key={c} className="flex gap-2">
                <span className="text-violet-soft">−</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-white">
            {data.productB.name} — pros & cons
          </h2>
          <ul className="mt-4 space-y-2 text-sm text-zinc-300">
            {data.b.pros.map((p) => (
              <li key={p} className="flex gap-2">
                <span className="text-amber-soft">+</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
          <ul className="mt-4 space-y-2 text-sm text-zinc-400">
            {data.b.cons.map((c) => (
              <li key={c} className="flex gap-2">
                <span className="text-violet-soft">−</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="section-title">Explore the products</h2>
        <p className="mt-2 text-sm text-zinc-400">
          Check current features, pricing, and usage limits on the official
          product sites.
        </p>
        <div className="mt-6 flex flex-col gap-4">
          <CtaButton
            affiliateId={data.productA.id}
            productName={data.productA.name}
          />
          <CtaButton
            affiliateId={data.productB.id}
            productName={data.productB.name}
          />
        </div>
      </section>

      <section className="mt-12">
        <h2 className="section-title">FAQ</h2>
        <div className="mt-6 space-y-3">
          {data.faq.map((item) => (
            <details
              key={item.q}
              className="card group open:border-violet-glow/30"
            >
              <summary className="cursor-pointer font-medium text-zinc-100">
                {item.q}
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-zinc-400">
                {item.a}
              </p>
            </details>
          ))}
        </div>
      </section>

      {data.notes?.length ? (
        <section className="mt-10 rounded-xl border border-ink-600/80 bg-ink-900/50 px-4 py-3 text-sm text-zinc-500">
          <p className="font-medium text-zinc-400">Notes</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <p className="mt-12 text-sm text-zinc-500">
        Prefer a shippable starter kit?{" "}
        <Link href="/forgekit" className="text-amber-soft hover:underline">
          ForgeKit
        </Link>{" "}
        · Buy on Gumroad for {SITE.forgekit.price}.
      </p>
    </article>
  );
}
