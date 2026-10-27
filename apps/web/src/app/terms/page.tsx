import type { Metadata } from "next";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE } from "../../../content/affiliates";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/terms/` },
  title: "Terms",
  description: "Terms of use and affiliate disclosure for AnderZilla.",
};

export default function TermsPage() {
  return (
    <div className="container-page py-16">
      <h1 className="text-4xl font-bold tracking-tight text-white">Terms of Use</h1>
      <p className="mt-2 text-sm text-zinc-500">Last updated: September 8, 2026</p>
      <div className="prose-dark mt-8 max-w-3xl">
        <p>
          By using {SITE.domain} you agree to these terms. Content is provided for
          informational and commercial purposes by {SITE.author} under the AnderZilla
          brand.
        </p>
        <h2>Products</h2>
        <p>
          Digital products such as ForgeKit are sold via third-party platforms (e.g.
          Gumroad). Their checkout terms, refunds, and delivery rules apply in addition
          to any product-specific license included with your purchase.
        </p>
        <h2>Content accuracy</h2>
        <p>
          StackPick comparisons and recommendations reflect editorial judgment. Tool
          features and pricing change — verify on the vendor&apos;s site before you buy.
          Official product links are provided alongside the comparisons.
        </p>
        <h2>Affiliate disclosure</h2>
        <AffiliateDisclosure className="not-prose my-4" />
        <h2>Limitation</h2>
        <p>
          The site is provided &quot;as is&quot; without warranties. To the fullest
          extent permitted by law, AnderZilla is not liable for indirect or consequential
          damages arising from use of the site or third-party services.
        </p>
        <h2>Contact</h2>
        <p>
          <a href={`mailto:${SITE.email}`}>{SITE.email}</a>
        </p>
      </div>
    </div>
  );
}
