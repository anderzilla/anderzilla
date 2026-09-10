import type { Metadata } from "next";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/privacy` },
  title: "Privacy",
  description: "Privacy policy and affiliate disclosure for AnderZilla.",
};

export default function PrivacyPage() {
  return (
    <div className="container-page py-16">
      <h1 className="text-4xl font-bold tracking-tight text-white">Privacy Policy</h1>
      <p className="mt-2 text-sm text-zinc-500">Last updated: September 8, 2026</p>
      <div className="prose-dark mt-8 max-w-3xl">
        <p>
          This policy describes how <strong className="text-white">{SITE.name}</strong> (
          {SITE.domain}) handles information when you visit the site or buy products.
        </p>
        <h2>What we collect</h2>
        <p>
          Basic server and analytics logs (IP, user agent, pages viewed) may be collected
          by hosting providers (e.g. Cloud Run, CDN). Product checkouts (Gumroad) are
          processed by those platforms under their own policies — AnderZilla does not
          store your full payment details.
        </p>
        <h2>Cookies</h2>
        <p>
          Essential cookies may be used for security and preferences. Third-party
          checkout or analytics tools may set their own cookies.
        </p>
        <h2>Affiliate links</h2>
        <AffiliateDisclosure className="not-prose my-4" />
        <p>
          Clicking an affiliate link may set a cookie so the partner can attribute a
          purchase. We do not sell your personal data.
        </p>
        <h2>Contact</h2>
        <p>
          Questions:{" "}
          <a href={`mailto:${SITE.email}`}>{SITE.email}</a>
        </p>
      </div>
    </div>
  );
}
