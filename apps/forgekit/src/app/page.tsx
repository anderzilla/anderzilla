import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { BuyButton } from "@/components/buy-button";

const GUMROAD_URL =
  process.env.NEXT_PUBLIC_GUMROAD_URL ?? "https://anderzilla.gumroad.com/l/edkel";
const DEMO_URL = "https://forgekit-kwzn5potra-rj.a.run.app";
const LINKEDIN_URL = "https://www.linkedin.com/in/andersonhenriquegoncalves";

const forWhom = [
  {
    title: "Indie founders shipping a paid digital product",
    body: "You need a clean Next.js MVP with landing, auth, entitlements, and a clear path to take payments — not another 50-package monorepo.",
  },
  {
    title: "Engineers who want ownership of the code",
    body: "You prefer a readable TypeScript codebase you can fork, deploy, and grow — Gumroad for delivery today, optional MoR checkout hooks when you are ready.",
  },
  {
    title: "Builders validating a SaaS-shaped idea",
    body: "Landing + gated dashboard + Prisma models give you a honest skeleton to customize without inventing session and entitlement plumbing from scratch.",
  },
];

const notFor = [
  {
    title: "No-code / drag-and-drop shoppers",
    body: "ForgeKit is source code. You will run Node, edit TypeScript, and deploy yourself (or with your engineer).",
  },
  {
    title: "People hunting a hosted SaaS",
    body: "You buy the ZIP and own the app. There is no AnderZilla-hosted multi-tenant product behind this purchase.",
  },
  {
    title: "Buyers who need hand-holding consulting",
    body: "Support means clear docs and reasonable product questions — not custom architecture workshops or unpaid agency work.",
  },
];

const deliverables = [
  {
    group: "App surfaces",
    items: [
      "Marketing landing with pricing CTA",
      "Login / register UI",
      "Gated /dashboard shell",
      "Buy CTA wired to Gumroad",
    ],
  },
  {
    group: "API & data",
    items: [
      "Auth routes: register, login, logout",
      "Checkout route shaped for MoR providers",
      "Webhook route for entitlement grants",
      "Prisma schema: User + Entitlement",
      "SQLite for local demos (Postgres-ready)",
    ],
  },
  {
    group: "Ops & docs",
    items: [
      "README + GETTING_STARTED.md",
      ".env.example for every required secret",
      "Dockerfile + Cloud Run deploy script",
      "DEMO_MODE for frictionless local explore",
    ],
  },
];

const stack = [
  "Next.js App Router",
  "React",
  "TypeScript",
  "Tailwind CSS",
  "Prisma",
  "SQLite → Postgres",
  "bcrypt sessions",
  "Docker / Cloud Run",
];

const zipContents = [
  "ForgeKit/ — full Next.js App Router source",
  "prisma/schema.prisma — User & Entitlement models",
  "src/app — landing, login, dashboard, API routes",
  "src/lib — auth, Prisma client, checkout helpers",
  "src/components — BuyButton, UI primitives",
  "Dockerfile + scripts/deploy-cloudrun.sh",
  ".env.example, package.json, lockfile, README",
];

const faqs = [
  {
    q: "What exactly do I get after purchase?",
    a: "A downloadable ZIP (ForgeKit-v0.1.0) from Gumroad plus GETTING_STARTED.md. Unzip, copy .env.example, install, push the Prisma schema, and run the Next.js app locally. You own the source under the buyer license.",
  },
  {
    q: "How does delivery work?",
    a: "Primary checkout is Gumroad (US$149, one-time). After payment you download the ZIP from your Gumroad library and follow GETTING_STARTED.md. No account on AnderZilla servers is required to receive the files.",
  },
  {
    q: "Is payment processing included?",
    a: "Buyers purchase ForgeKit on Gumroad. Inside the kit, checkout and webhook routes are structured as a checkout-ready architecture so you can wire your own merchant-of-record or payment provider when you sell your product. Gumroad covers delivery of this starter; your product’s live billing is yours to connect.",
  },
  {
    q: "Can I use Postgres in production?",
    a: "Yes. Change the Prisma datasource provider and DATABASE_URL. The User and Entitlement models stay the same.",
  },
  {
    q: "What is the license?",
    a: "Perpetual license to use and modify ForgeKit in personal and commercial projects. You may not resell the unmodified starter as a competing template or publish the raw source as a free clone. Attribution is appreciated, not required.",
  },
  {
    q: "What support should I expect?",
    a: "Docs-first: README, GETTING_STARTED, and .env.example. Reasonable product questions after purchase are welcome. Custom feature work, production debugging retainers, and architecture consulting are out of scope for the US$149 license.",
  },
  {
    q: "Who built this?",
    a: "AnderZilla — Senior Software Engineer / hands-on architect with 15+ years shipping production systems across mobile, web, and backend.",
  },
];

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(245,158,11,0.12),_transparent_55%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent" />

      <header className="relative z-10 mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 text-sm font-bold text-zinc-950">
            F
          </span>
          <span>
            ForgeKit
            <span className="ml-2 hidden text-xs font-normal text-zinc-500 sm:inline">
              by AnderZilla
            </span>
          </span>
        </div>
        <nav className="hidden items-center gap-4 text-sm text-zinc-400 sm:flex">
          <a href="#for-whom" className="hover:text-zinc-100">
            Fit
          </a>
          <a href="#inside" className="hover:text-zinc-100">
            Inside
          </a>
          <a href="#builder" className="hover:text-zinc-100">
            Builder
          </a>
          <a href="#faq" className="hover:text-zinc-100">
            FAQ
          </a>
          <a href={DEMO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-zinc-100">
            Demo
          </a>
          <a href="#buy">
            <Button size="sm">Buy on Gumroad</Button>
          </a>
        </nav>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-5xl px-6 pb-24">
        {/* 1. Hero */}
        <section className="flex flex-col items-start gap-8 py-16 md:py-24">
          <p className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium tracking-wide text-amber-300">
            Next.js digital product kit · One-time US$149 · Gumroad delivery
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-zinc-50 md:text-6xl md:leading-[1.05]">
            A serious Next.js MVP you can sell from — without the bloat.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-zinc-400">
            ForgeKit is a focused starter for founders and engineers: marketing landing,
            auth, Prisma entitlements, gated dashboard, and a checkout-ready architecture.
            Buy once on Gumroad, download the ZIP, and ship on your own terms.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href={GUMROAD_URL} target="_blank" rel="noopener noreferrer">
              <Button size="lg">Buy on Gumroad — US$149</Button>
            </a>
            <a href={DEMO_URL} target="_blank" rel="noopener noreferrer">
              <Button size="lg" variant="secondary">
                Try live demo
              </Button>
            </a>
            <Link href="/dashboard">
              <Button size="lg" variant="ghost">
                Demo dashboard
              </Button>
            </Link>
          </div>
          <p className="text-sm text-zinc-500">
            By{" "}
            <span className="text-zinc-300">AnderZilla</span>
            {" · "}
            Senior Software Engineer / hands-on architect · 15+ years production systems
          </p>
        </section>

        {/* 2. Who it's for / not for */}
        <section id="for-whom" className="scroll-mt-20 py-12">
          <div className="mb-8 max-w-2xl">
            <h2 className="text-2xl font-semibold tracking-tight">Who it&apos;s for — and who it&apos;s not</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-400">
              Clear fit beats vague promises. Buy if this matches how you work.
            </p>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-amber-300/90">
                Good fit
              </p>
              <div className="space-y-3">
                {forWhom.map((item) => (
                  <Card key={item.title} className="p-5">
                    <h3 className="font-medium text-zinc-100">{item.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-zinc-400">{item.body}</p>
                  </Card>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Not a fit
              </p>
              <div className="space-y-3">
                {notFor.map((item) => (
                  <Card key={item.title} className="border-zinc-800/80 bg-zinc-950/40 p-5">
                    <h3 className="font-medium text-zinc-200">{item.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-zinc-500">{item.body}</p>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 3. What's inside */}
        <section id="inside" className="scroll-mt-20 py-12">
          <div className="mb-8 max-w-2xl">
            <h2 className="text-2xl font-semibold tracking-tight">What&apos;s inside</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-400">
              Concrete deliverables from the ZIP — the same codebase that powers the live demo.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {deliverables.map((col) => (
              <Card key={col.group}>
                <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-amber-300/90">
                  {col.group}
                </h3>
                <ul className="space-y-2.5">
                  {col.items.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm text-zinc-300">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>

          <Card className="mt-4">
            <h3 className="mb-3 text-lg font-medium text-zinc-50">What&apos;s in the ZIP</h3>
            <ul className="grid gap-2 sm:grid-cols-2">
              {zipContents.map((item) => (
                <li key={item} className="flex items-start gap-2 font-mono text-xs leading-5 text-zinc-400">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-zinc-600" />
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-xs text-zinc-500">
              No node_modules, no .env secrets, no databases in the download. Install from the lockfile after unzip.
            </p>
          </Card>
        </section>

        {/* Mid CTA */}
        <section id="buy" className="scroll-mt-20 py-8">
          <Card className="border-amber-500/30 bg-gradient-to-br from-zinc-900 to-zinc-950">
            <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm font-medium text-amber-300">One-time license</p>
                <h2 className="mt-1 text-3xl font-semibold tracking-tight">US$149</h2>
                <p className="mt-2 max-w-md text-sm leading-6 text-zinc-400">
                  Pay once on Gumroad. Download the ZIP, follow GETTING_STARTED.md, and run
                  locally. The live demo stays free to explore.
                </p>
                <p className="mt-3 text-xs text-zinc-500">
                  License · perpetual commercial use · no resale of the unmodified starter
                </p>
              </div>
              <BuyButton />
            </div>
          </Card>
        </section>

        {/* 4. Built by AnderZilla */}
        <section id="builder" className="scroll-mt-20 py-12">
          <Card className="overflow-hidden p-0">
            <div className="grid md:grid-cols-[1fr_auto]">
              <div className="p-6 md:p-8">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-300/90">
                  Built by AnderZilla
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-50">
                  Senior engineer. Hands-on architect.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
                  AnderZilla is a Senior Software Engineer and hands-on architect with 15+ years
                  building production systems across mobile, web, and backend — in banking,
                  industrial, and agritech contexts. Daily stack includes Python, FastAPI, React,
                  Next.js, TypeScript, and React Native. Based in Curitiba, Brazil; works remote.
                  ForgeKit is an indie product from that practice: opinionated where it saves time,
                  honest about what you still wire yourself.
                </p>
                <a
                  href={LINKEDIN_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-5 inline-flex text-sm font-medium text-amber-300 hover:text-amber-200"
                >
                  AnderZilla on LinkedIn →
                </a>
              </div>
              <div className="flex flex-col justify-center gap-3 border-t border-zinc-800 bg-zinc-950/50 p-6 md:border-l md:border-t-0 md:px-8">
                <p className="text-xs uppercase tracking-wider text-zinc-500">Focus</p>
                <ul className="space-y-2 text-sm text-zinc-300">
                  <li>Production systems</li>
                  <li>Mobile · web · backend</li>
                  <li>Banking · industrial · agritech</li>
                  <li>Curitiba BR · remote</li>
                </ul>
              </div>
            </div>
          </Card>
        </section>

        {/* 5. Stack badges */}
        <section id="stack" className="scroll-mt-20 py-12">
          <h2 className="mb-6 text-2xl font-semibold tracking-tight">Stack</h2>
          <div className="flex flex-wrap gap-2">
            {stack.map((item) => (
              <span
                key={item}
                className="rounded-full border border-zinc-800 bg-zinc-900/80 px-3.5 py-1.5 text-sm text-zinc-300"
              >
                {item}
              </span>
            ))}
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-500">
            Checkout-ready routes and webhook handlers are included so you can connect Gumroad
            delivery today and optional merchant-of-record hooks when your own product needs them.
          </p>
        </section>

        {/* Support / license strip */}
        <section className="py-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="p-5">
              <h3 className="font-medium text-zinc-100">License</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Perpetual use and modification in commercial projects. No reselling the unmodified
                starter as a competing template. Attribution optional.
              </p>
            </Card>
            <Card className="p-5">
              <h3 className="font-medium text-zinc-100">Support expectations</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                Docs-first (GETTING_STARTED + README). Reasonable product questions after purchase.
                Not included: custom builds, unpaid consulting, or production on-call.
              </p>
            </Card>
          </div>
        </section>

        {/* 6. FAQ */}
        <section id="faq" className="scroll-mt-20 py-12">
          <h2 className="mb-6 text-2xl font-semibold tracking-tight">FAQ</h2>
          <div className="space-y-3">
            {faqs.map((item) => (
              <Card key={item.q} className="p-5">
                <h3 className="font-medium text-zinc-100">{item.q}</h3>
                <p className="mt-2 text-sm leading-6 text-zinc-400">{item.a}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* 7. Final CTA */}
        <section className="py-12">
          <Card className="border-amber-500/20 bg-gradient-to-b from-zinc-900/80 to-zinc-950 text-center">
            <p className="text-sm font-medium text-amber-300">Ready to ship your own product shell?</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-50">
              Get ForgeKit — US$149
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-zinc-400">
              One-time Gumroad purchase. ZIP delivery. Clear English docs. Built by AnderZilla —
              no fake testimonials, no invented metrics.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a href={GUMROAD_URL} target="_blank" rel="noopener noreferrer">
                <Button size="lg">Buy on Gumroad — US$149</Button>
              </a>
              <a href={DEMO_URL} target="_blank" rel="noopener noreferrer">
                <Button size="lg" variant="secondary">
                  Try live demo
                </Button>
              </a>
            </div>
          </Card>
        </section>
      </main>

      <footer className="relative z-10 border-t border-zinc-900 py-8 text-center text-sm text-zinc-500">
        <p>
          ForgeKit · by AnderZilla · {new Date().getFullYear()}
        </p>
        <p className="mt-2 text-xs text-zinc-600">
          <a href={LINKEDIN_URL} className="hover:text-zinc-400" target="_blank" rel="noopener noreferrer">
            LinkedIn
          </a>
          {" · "}
          <a href={GUMROAD_URL} className="hover:text-zinc-400" target="_blank" rel="noopener noreferrer">
            Gumroad
          </a>
          {" · "}
          <a href={DEMO_URL} className="hover:text-zinc-400" target="_blank" rel="noopener noreferrer">
            Live demo
          </a>
        </p>
      </footer>
    </div>
  );
}
