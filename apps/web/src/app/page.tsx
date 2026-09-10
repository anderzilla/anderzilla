import type { Metadata } from "next";
import Link from "next/link";
import { NewsletterCapture } from "@/components/NewsletterCapture";
import { SITE } from "../../content/affiliates";
import { listComparisons } from "../../content/stackpick";

export const metadata: Metadata = {
  title: { absolute: `${SITE.name} — ${SITE.tagline}` },
};

const audiences = [
  {
    title: "Programmers",
    blurb: "Ship faster with opinionated kits, stack comparisons, and zero-ceremony docs.",
    icon: "</>",
  },
  {
    title: "Gamers",
    blurb: "Latency, builds, and gear that actually matter — not sponsored fluff.",
    icon: "▶",
  },
  {
    title: "Nerds & geeks",
    blurb: "Deep dives, weird tech rabbit holes, and culture that respects the craft.",
    icon: "◆",
  },
];

const techBits = [
  "Next.js & TypeScript",
  "Cloud Run & containers",
  "AI tooling that earns its keep",
  "Indie product loops",
];

export default function HomePage() {
  const comparisons = listComparisons().slice(0, 5);

  return (
    <>
      <section className="relative overflow-hidden border-b border-ink-600/40">
        <div
          className="pointer-events-none absolute inset-0 bg-grid-fade bg-[size:32px_32px] opacity-60"
          aria-hidden
        />
        <div className="container-page relative py-20 sm:py-28">
          <p className="badge mb-4">AnderZilla · indie · USD</p>
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Build, ship, and{" "}
            <span className="bg-gradient-to-r from-amber-glow to-violet-soft bg-clip-text text-transparent">
              geek out
            </span>{" "}
            without the cringe.
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-zinc-300">
            Hi — I&apos;m <strong className="text-white">AnderZilla</strong>.
            This is my personal hub for developers, gamers, and tech nerds: products that
            pay for themselves, honest stack picks, and future gear drops. Not a corporate
            consultancy site.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href={SITE.forgekit.gumroad}
              className="btn-primary"
              target="_blank"
              rel="noopener noreferrer"
            >
              Buy on Gumroad — {SITE.forgekit.price}
            </a>
            <a
              href={SITE.forgekit.demo}
              className="btn-secondary"
              target="_blank"
              rel="noopener noreferrer"
            >
              Live demo
            </a>
            <Link href="/forgekit" className="btn-ghost">
              ForgeKit details
            </Link>
          </div>
          <p className="mt-6 font-mono text-xs text-zinc-500">
            geist · dark UX · performance-first · no clutter ads
          </p>
        </div>
      </section>

      <section className="container-page py-16">
        <h2 className="section-title">Who this is for</h2>
        <p className="mt-2 max-w-2xl muted">
          Sharp, friendly, geek-culture OK. If you write code, push ranked, or collect
          mechanical keyboards — you&apos;re home.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {audiences.map((a) => (
            <article key={a.title} className="card">
              <span className="font-mono text-amber-soft">{a.icon}</span>
              <h3 className="mt-3 text-lg font-semibold text-white">{a.title}</h3>
              <p className="mt-2 text-sm text-zinc-400">{a.blurb}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-ink-600/40 bg-ink-900/50">
        <div className="container-page py-16">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="badge">Featured product</p>
              <h2 className="section-title mt-3">ForgeKit</h2>
              <p className="mt-2 max-w-xl text-zinc-300">{SITE.forgekit.blurb}</p>
            </div>
            <p className="text-3xl font-bold text-amber-soft">{SITE.forgekit.price}</p>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href={SITE.forgekit.gumroad}
              className="btn-primary"
              target="_blank"
              rel="noopener noreferrer"
            >
              Buy on Gumroad — {SITE.forgekit.price}
            </a>
            <a
              href={SITE.forgekit.demo}
              className="btn-secondary"
              target="_blank"
              rel="noopener noreferrer"
            >
              Open live demo
            </a>
            <Link href="/forgekit" className="btn-ghost">
              Full details
            </Link>
          </div>
        </div>
      </section>

      <section className="container-page py-16">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="badge">pSEO hub</p>
            <h2 className="section-title mt-3">StackPick</h2>
            <p className="mt-2 max-w-xl text-zinc-300">
              Wirecutter-lite comparisons — TL;DR, tables, pros/cons, FAQ. Affiliate CTAs
              stay placeholders until real programs are approved. No invented partnerships.
            </p>
          </div>
          <Link href="/stackpick" className="btn-secondary shrink-0">
            All comparisons
          </Link>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {comparisons.map((c) => (
            <Link
              key={c.slug}
              href={`/stackpick/${c.slug}`}
              className="card transition hover:border-violet-soft/40"
            >
              <span className="badge">{c.category}</span>
              <h3 className="mt-3 font-semibold text-white">{c.title}</h3>
              <p className="mt-2 text-sm text-zinc-400">{c.teaser}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="container-page pb-8">
        <NewsletterCapture />
      </section>

      <section className="container-page py-16">
        <h2 className="section-title">Geek · Gamer · Tech</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <article className="card">
            <h3 className="text-lg font-semibold text-white">Tech that ships</h3>
            <ul className="mt-4 space-y-2 text-sm text-zinc-400">
              {techBits.map((t) => (
                <li key={t} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-violet-glow" />
                  {t}
                </li>
              ))}
            </ul>
          </article>
          <article className="card">
            <h3 className="text-lg font-semibold text-white">Coming up</h3>
            <ul className="mt-4 space-y-4">
              {SITE.future.map((f) => (
                <li key={f.id}>
                  <p className="font-medium text-zinc-200">{f.name}</p>
                  <p className="text-sm text-zinc-400">{f.blurb}</p>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>
    </>
  );
}
