import type { Metadata } from "next";
import Link from "next/link";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
  title: "ForgeKit",
  description: `${SITE.forgekit.blurb} Buy ForgeKit for ${SITE.forgekit.price} on Gumroad.`,
  openGraph: {
    title: `ForgeKit · ${SITE.name}`,
    description: SITE.forgekit.blurb,
    url: `${SITE.url}/forgekit`,
  },
};

const features = [
  {
    title: "Landing + auth + gated dashboard",
    body: "Next.js App Router marketing page, email/password sessions, DEMO_MODE, and a /dashboard shell with Prisma entitlements.",
  },
  {
    title: "Checkout-ready architecture",
    body: "Gumroad for kit delivery today, plus structured checkout/webhook routes so you can wire optional MoR hooks for your own product.",
  },
  {
    title: "Cloud-ready from day one",
    body: "Dockerfile and Cloud Run deploy script included. SQLite locally; Postgres-ready Prisma schema.",
  },
  {
    title: "Opinionated, not religious",
    body: "Clear TypeScript defaults with room to swap pieces. No cargo-cult frameworks or fake metrics.",
  },
];

export default function ForgeKitPage() {
  return (
    <div className="container-page py-16">
      <p className="badge">Digital product · Gumroad</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        ForgeKit
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-zinc-300">{SITE.forgekit.blurb}</p>
      <p className="mt-4 text-3xl font-bold text-amber-soft">{SITE.forgekit.price}</p>
      <p className="mt-2 text-sm text-zinc-500">
        By AnderZilla — Senior Software Engineer / hands-on architect · indie product, not a faceless brand.
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
      </div>

      <div className="mt-14 grid gap-4 sm:grid-cols-2">
        {features.map((f) => (
          <article key={f.title} className="card">
            <h2 className="text-lg font-semibold text-white">{f.title}</h2>
            <p className="mt-2 text-sm text-zinc-400">{f.body}</p>
          </article>
        ))}
      </div>

      <section className="mt-14 card border-amber-glow/30 shadow-glow">
        <h2 className="text-xl font-semibold text-white">Ready when you are</h2>
        <p className="mt-2 text-zinc-400">
          Primary checkout is on Gumroad. After purchase you download the ZIP and follow
          GETTING_STARTED.md — delivery from AnderZilla, no hosted multi-tenant SaaS.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
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
            className="btn-ghost"
            target="_blank"
            rel="noopener noreferrer"
          >
            Demo · {SITE.forgekit.demo.replace("https://", "")}
          </a>
        </div>
        <p className="mt-4">
          <Link href="/stackpick" className="text-sm text-violet-soft hover:underline">
            Also browsing tools? See StackPick →
          </Link>
        </p>
      </section>
    </div>
  );
}
