import Link from "next/link";
import { SITE } from "../../content/affiliates";

const nav = [
  { href: "/forgekit", label: "ForgeKit" },
  { href: "/stackpick", label: "StackPick" },
  { href: "/about", label: "About" },
  { href: "/links", label: "Links" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-ink-600/60 bg-ink-950/80 backdrop-blur-md">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Link href="/" className="group flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-glow to-violet-glow text-sm font-bold text-ink-950">
            Az
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-white transition group-hover:text-amber-soft">
              AnderZilla
            </span>
            <span className="mt-0.5 font-mono text-[10px] font-normal text-zinc-500">
              ship notes
            </span>
          </span>
        </Link>
        <nav className="hidden items-center gap-1 sm:flex">
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
          Buy on Gumroad
        </a>
      </div>
    </header>
  );
}
