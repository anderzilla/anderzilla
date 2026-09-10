import type { Metadata } from "next";
import Link from "next/link";
import { Credibility } from "@/components/Credibility";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/about` },
  title: "About",
  description: `About AnderZilla — ${SITE.role} building from ${SITE.location}.`,
};

export default function AboutPage() {
  return (
    <div className="container-page py-16">
      <p className="badge">Indie · remote · personal brand</p>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
        About AnderZilla
      </h1>
      <div className="prose-dark mt-8 max-w-2xl">
        <p>
          <strong className="text-white">AnderZilla</strong> is the personal brand of a{" "}
          {SITE.role} based in {SITE.location} — 15+ years shipping production systems
          across mobile, web, and backend (banking, industrial, agritech).
        </p>
        <p>
          Explore the <Link href="/forgekit">ForgeKit</Link> software starter and
          <Link href="/stackpick"> StackPick</Link> tool comparisons. Each is built around
          helping you understand your options and make progress on your own projects.
        </p>
        <h2>What I care about</h2>
        <p>
          Readable code, useful documentation, and clear technical tradeoffs. This is a
          space for programmers, gamers, and tech enthusiasts who enjoy understanding
          how things work.
        </p>
        <h2>Where I work</h2>
        <p>
          Curitiba, Brazil — fully remote with clients and products worldwide. Primary UI
          and pricing here are English / USD for a global audience.
        </p>
      </div>
      <div className="mt-12"><Credibility /></div>
      <div className="mt-10 flex flex-wrap gap-3">
        <a
          href={SITE.forgekit.gumroad}
          className="btn-primary"
          target="_blank"
          rel="noopener noreferrer"
        >
          Buy on Gumroad — {SITE.forgekit.price}
        </a>
        <Link href="/links" className="btn-secondary">
          All links
        </Link>
      </div>
    </div>
  );
}
