import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { SITE } from "../../content/affiliates";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: `${SITE.name} — ${SITE.tagline}`,
    template: `%s · ${SITE.name}`,
  },
  description:
    "AnderZilla is a personal brand hub — ForgeKit, StackPick, and tools for programmers, gamers, and tech nerds.",
  keywords: [
    "AnderZilla",
    "ForgeKit",
    "StackPick",
    "indie developer",
    "software engineer",
    "developer tools",
    "AI comparisons",
  ],
  authors: [{ name: SITE.author, url: SITE.url }],
  creator: SITE.author,
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE.url,
    siteName: SITE.name,
    title: `${SITE.name} — ${SITE.tagline}`,
    description:
      "Products and stack picks for builders who ship. ForgeKit, StackPick, and more.",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "AnderZilla",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE.name} — ${SITE.tagline}`,
    description: "Tools, stacks & geek fuel for builders who ship.",
    images: ["/og.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.svg",
  },
  alternates: {
    canonical: SITE.url,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen font-sans`}
      >
        <div className="flex min-h-screen flex-col bg-hero-glow bg-ink-950">
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
