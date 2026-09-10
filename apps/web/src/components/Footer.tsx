import Link from "next/link";
import { AffiliateDisclosure } from "@/components/AffiliateDisclosure";
import { SITE } from "../../content/affiliates";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-24 border-t border-ink-600/60 bg-ink-900/40">
      <div className="container-page grid gap-8 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="font-semibold text-white">AnderZilla</p>
          <p className="mt-2 text-sm text-zinc-400">
            Personal brand hub — products, stack picks, and geek fuel.
            Not a consultancy Inc.
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
            <li>
              <span className="text-zinc-500">Gear31.club · soon</span>
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
          <p className="text-sm font-semibold text-zinc-200">Locale</p>
          <p className="mt-3 text-sm text-zinc-400">
            UI in English · prices in USD · Curitiba · remote worldwide
          </p>
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
          <p className="font-mono text-[11px]">engineering geek · dark UX · ship notes</p>
        </div>
      </div>
    </footer>
  );
}
