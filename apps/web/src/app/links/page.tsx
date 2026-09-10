import type { Metadata } from "next";
import Link from "next/link";
import { SITE, SOCIAL_CHANNELS } from "../../../content/affiliates";

export const metadata: Metadata = {
  alternates: { canonical: `${SITE.url}/links` },
  title: "Links",
  description: "Find AnderZilla on YouTube, TikTok, Instagram, Twitch, and Kick. Explore StackPick and ForgeKit.",
};

const links = [
  ...SOCIAL_CHANNELS.map((channel) => ({
    ...channel,
    external: true,
    primary: false,
  })),
  {
    href: SITE.forgekit.gumroad,
    label: `Buy on Gumroad — ${SITE.forgekit.price}`,
    external: true,
    primary: true,
  },
  {
    href: SITE.forgekit.demo,
    label: "ForgeKit live demo",
    external: true,
    primary: false,
  },
  { href: "/forgekit", label: "ForgeKit product page", external: false, primary: false },
  { href: "/stackpick", label: "StackPick hub", external: false, primary: false },
  { href: "/about", label: "About AnderZilla", external: false, primary: false },
  {
    href: SITE.social.github,
    label: "GitHub",
    external: true,
    primary: false,
  },
];

export default function LinksPage() {
  return (
    <div className="container-page flex max-w-lg flex-col py-16">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-glow to-violet-glow text-xl font-bold text-ink-950">
          Az
        </div>
        <h1 className="mt-4 text-2xl font-bold text-white">AnderZilla</h1>
        <p className="mt-1 text-sm text-zinc-400">{SITE.tagline}</p>
      </div>
      <ul className="mt-10 space-y-3">
        {links.map((l) => {
          const className = l.primary
            ? "btn-primary w-full"
            : "btn-secondary w-full justify-between";
          if (l.external) {
            return (
              <li key={l.href}>
                <a
                  href={l.href}
                  className={className}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {l.label}
                </a>
              </li>
            );
          }
          return (
            <li key={l.href}>
              <Link href={l.href} className={className}>
                {l.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
