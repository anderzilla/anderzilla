import { BrandWordmark } from "./BrandAssets";
import Link from "next/link";
import { SITE } from "../../content/affiliates";

const nav = [
  { href: "/forgekit/", label: "ForgeKit" },
  { href: "/stackpick/", label: "StackPick" },
  { href: "/about/", label: "About" },
  { href: "/links/", label: "Links" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-ink-600/60 bg-ink-950/80 backdrop-blur-md">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Link
          href="/"
          className="group flex items-center gap-2 font-semibold tracking-tight"
        >
          <BrandWordmark className="az-wordmark-legacy" />
        </Link>
        <nav
          aria-label="Main navigation"
          className="hidden items-center gap-1 md:flex"
        >
          {nav.map((item) => (
            <Link key={item.href} href={item.href} className="btn-ghost">
              {item.label}
            </Link>
          ))}
        </nav>
        <a
          href={SITE.forgekit.gumroad}
          className="btn-primary text-xs sm:text-sm"
          target="_blank"
          rel="noopener noreferrer"
        >
          Buy ForgeKit
        </a>
      </div>
      <nav
        aria-label="Mobile navigation"
        className="container-page flex flex-wrap gap-1 pb-3 md:hidden"
      >
        {nav.map((item) => (
          <Link key={item.href} href={item.href} className="btn-ghost">
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

