import type { Metadata } from "next";
import Link from "next/link";
import { Credibility } from "@/components/Credibility";
import { SITE } from "../../content/affiliates";
import { listComparisons } from "../../content/stackpick";

export const metadata: Metadata = {
  title: { absolute: `${SITE.name} — ${SITE.tagline}` },
};

export default function HomePage() {
  const comparisons = listComparisons();
  return (
    <>
      <section className="relative overflow-hidden border-b border-ink-600/40">
        <div
          className="pointer-events-none absolute inset-0 bg-grid-fade bg-[size:32px_32px] opacity-40"
          aria-hidden
        />
        <div className="container-page relative grid gap-12 py-16 sm:py-24 lg:grid-cols-[1.2fr_1fr] lg:items-center">
          <div>
            <p className="badge">Tech · AI · Games · Gadgets</p>
            <h1 className="mt-6 max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Stay curious.
              <br />
              <span className="text-amber-soft">Make room for fun.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-300">
              Welcome to my corner of the internet. I&apos;m AnderZilla — into
              new tech, AI experiments, games, and gadgets. A place to explore
              what makes technology useful, surprising, and fun.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/links" className="btn-primary">
                Find my channels
              </Link>
              <Link href="/stackpick" className="btn-secondary">
                Browse StackPick
              </Link>
            </div>
            <p className="mt-6 text-sm text-zinc-400">
              Personal curiosity. A builder&apos;s eye for detail.
            </p>
          </div>
          <article className="card border-amber-glow/30 bg-ink-950/90 p-6 sm:p-8">
            <div className="flex items-center justify-between gap-3">
              <span className="badge">Featured product</span>
              <span className="code-chip">v0.1.0</span>
            </div>
            <h2 className="mt-6 text-3xl font-semibold text-white">ForgeKit</h2>
            <p className="mt-3 leading-relaxed text-zinc-300">
              A focused Next.js starting point for your next digital product.
            </p>
            <ul className="my-6 space-y-3 border-y border-ink-600/60 py-6 text-sm text-zinc-300">
              <li>Landing page, email/password auth, gated dashboard</li>
              <li>Prisma data models and deployment files</li>
              <li>Downloadable source code + getting started guide</li>
            </ul>
            <p className="text-3xl font-semibold text-white">
              {SITE.forgekit.price}
              <span className="ml-2 text-sm font-normal text-zinc-400">
                one-time
              </span>
            </p>
            <a
              href={SITE.forgekit.gumroad}
              className="btn-primary mt-5 w-full"
              target="_blank"
              rel="noopener noreferrer"
            >
              Buy ForgeKit on Gumroad
            </a>
            <a
              href={SITE.forgekit.demo}
              className="btn-ghost mt-2 w-full"
              target="_blank"
              rel="noopener noreferrer"
            >
              Explore the live demo →
            </a>
            <p className="mt-3 text-xs leading-relaxed text-zinc-400">
              Source code you customize and deploy. Connect your own payment
              provider before accepting payments in your app.
            </p>
          </article>
        </div>
      </section>
      <section className="container-page py-16 sm:py-20">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="badge">StackPick / Developer tools</p>
            <h2 className="section-title mt-3">Understand the tradeoffs.</h2>
            <p className="mt-3 max-w-2xl text-zinc-300">
              Compare hosting, databases, auth, AI editors, and GPU platforms.
              Start with your use case, then explore each option side by side.
            </p>
          </div>
          <Link href="/stackpick" className="btn-secondary">
            All comparisons →
          </Link>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {comparisons.map((c) => (
            <Link
              key={c.slug}
              href={`/stackpick/${c.slug}`}
              className="card flex flex-col transition hover:border-violet-soft/50"
            >
              <span className="badge w-fit">{c.category}</span>
              <h3 className="mt-4 text-lg font-semibold text-white">
                {c.title}
              </h3>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-zinc-400">
                {c.teaser}
              </p>
              <span className="mt-6 text-sm font-medium text-amber-soft">
                Read comparison →
              </span>
            </Link>
          ))}
        </div>
      </section>
      <section className="container-page pb-16">
        <Credibility />
      </section>
    </>
  );
}
