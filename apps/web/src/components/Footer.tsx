import Link from "next/link";
import { BrandWordmark } from "./BrandAssets";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE, SOCIAL_CHANNELS } from "../../content/affiliates";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-8 border-t border-ink-600/60 bg-ink-900/40">
      <div className="container-page grid gap-8 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <Link href="/" className="brand-footer"><BrandWordmark /></Link>
          <p className="mt-2 text-sm text-zinc-400">
            My corner of tech, AI, games, and gadgets. Stay curious, try things,
            and have some fun.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-200">Products</p>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            <li>
              <Link href="/forgekit" className="hover:text-amber-soft">
                ForgeKit
              </Link>
            </li>
            <li>
              <a
                href={SITE.forgekit.gumroad}
                className="hover:text-amber-soft"
                target="_blank"
                rel="noopener noreferrer"
              >
                Buy on Gumroad
              </a>
            </li>
            <li>
              <Link href="/stackpick" className="hover:text-amber-soft">
                StackPick
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-200">Site</p>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            <li>
              <Link href="/about" className="hover:text-amber-soft">
                About
              </Link>
            </li>
            <li>
              <Link href="/links" className="hover:text-amber-soft">
                Links
              </Link>
            </li>
            <li>
              <Link href="/privacy" className="hover:text-amber-soft">
                Privacy
              </Link>
            </li>
            <li>
              <Link href="/terms" className="hover:text-amber-soft">
                Terms
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-200">Find me online</p>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            {SOCIAL_CHANNELS.map((channel) => (
              <li key={channel.href}>
                <a
                  href={channel.href}
                  className="hover:text-amber-soft"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {channel.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="container-page pb-8">
        <AffiliateDisclosure compact />
      </div>
      <div className="border-t border-ink-600/40">
        <div className="container-page flex flex-col gap-2 py-6 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {year} AnderZilla
          </p>
          <p className="font-mono text-[11px]">Build · play · explore</p>
        </div>
      </div>
    </footer>
  );
}

