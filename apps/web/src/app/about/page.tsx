import type { Metadata } from "next";
import Link from "next/link";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
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
          This site is the monetization hub: digital products (
          <Link href="/forgekit">ForgeKit</Link>), comparison content (
          <Link href="/stackpick">StackPick</Link>), and upcoming projects like Gear31.club
          and a newsletter. It is <em>not</em> a consultancy brand — consulting lives
          elsewhere.
        </p>
        <h2>What I care about</h2>
        <p>
          Shipping real software, keeping architecture honest, and talking to programmers,
          gamers, and nerds without the motivational-poster voice. Geek culture welcome;
          cringe optional (preferably off).
        </p>
        <h2>Where I work</h2>
        <p>
          Curitiba, Brazil — fully remote with clients and products worldwide. Primary UI
          and pricing here are English / USD for a global audience.
        </p>
      </div>
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
