import type { Metadata } from "next";
import Link from "next/link";
import { Credibility } from "@/components/Credibility";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/forgekit` },
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
    body: "A marketing page, email/password login, and a dashboard starting point with Prisma access models. Demo mode lets you explore the app.",
  },
  {
    title: "Payment integration starting points",
    body: "Receive the kit through Gumroad. Checkout and webhook route examples are included; connecting and testing your own payment provider is required before taking payments.",
  },
  {
    title: "Deployment files included",
    body: "Dockerfile and Cloud Run deploy script included. SQLite locally; Postgres-ready Prisma schema.",
  },
  {
    title: "Readable TypeScript foundations",
    body: "A focused codebase to adapt to your product, with setup documentation and room to change the stack as your requirements grow.",
  },
];

export default function ForgeKitPage() {
  return (
    <div className="container-page py-16">
      <p className="badge">Digital product · Gumroad</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        ForgeKit
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-zinc-300">
        {SITE.forgekit.blurb}
      </p>
      <p className="mt-4 text-3xl font-bold text-amber-soft">
        {SITE.forgekit.price}{" "}
        <span className="text-sm font-normal text-zinc-400">one-time</span>
      </p>
      <p className="mt-2 text-sm text-zinc-500">
        By AnderZilla — Senior Software Engineer / hands-on architect · 15+
        years building production systems.
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

      <section className="mt-14 grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="text-xl font-semibold">Your download</h2>
          <p className="mt-3 leading-relaxed text-zinc-400">
            ForgeKit-v0.1.0.zip and GETTING_STARTED.md, delivered through
            Gumroad. Includes the application source, Prisma models, environment
            example, Dockerfile, and Cloud Run deployment script.
          </p>
        </div>
        <div className="card">
          <h2 className="text-xl font-semibold">Before you buy</h2>
          <p className="mt-3 leading-relaxed text-zinc-400">
            For developers comfortable with Node.js and TypeScript. You
            configure hosting, database access, and payment processing for your
            product. The purchase is a source-code download; hosting and custom
            development are separate.
          </p>
        </div>
      </section>
      <div className="mt-14">
        <Credibility />
      </div>
      <section className="mt-14 card border-amber-glow/30 shadow-glow">
        <h2 className="text-xl font-semibold text-white">Ready when you are</h2>
        <p className="mt-2 text-zinc-400">
          Purchase on Gumroad, download the ZIP and setup guide, then start
          building locally. The live demo is available to explore before you
          buy.
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
            Explore the live demo →
          </a>
        </div>
        <p className="mt-4">
          <Link
            href="/stackpick"
            className="text-sm text-violet-soft hover:underline"
          >
            Also browsing tools? See StackPick →
          </Link>
        </p>
      </section>
    </div>
  );
}
