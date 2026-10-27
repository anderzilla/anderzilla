import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Oxanium, Space_Grotesk } from "next/font/google";
import { SiteFrame } from "@/components/SiteFrame";
import { SITE } from "../../content/affiliates";
import "./globals.css";
import "./brand.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const oxanium = Oxanium({
  variable: "--font-brand-display",
  subsets: ["latin"],
});
const spaceGrotesk = Space_Grotesk({
  variable: "--font-brand-body",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: `${SITE.name} — Games, IA e boas descobertas`,
    template: `%s · ${SITE.name}`,
  },
  description:
    "Games, AI, gadgets and great discoveries with AnderZilla. Explore the radar, challenges, streams and Karaca Points.",
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
    locale: "pt_BR",
    url: SITE.url,
    siteName: SITE.name,
    title: `${SITE.name} — Games, IA e boas descobertas`,
    description: "Games, AI, gadgets and great discoveries with AnderZilla.",
    images: [
      {
        url: "/brand/social-card.png",
        width: 1200,
        height: 630,
        alt: "AnderZilla",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE.name} — Games, IA e boas descobertas`,
    description: "Games, AI, gadgets and great discoveries.",
    images: ["/brand/social-card.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }, { url: "/brand/favicon.ico", sizes: "any" }, { url: "/brand/favicon-32.png", type: "image/png", sizes: "32x32" }],
    apple: [{ url: "/brand/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  alternates: {
    canonical: `${SITE.url}/`,
  },
};

export const viewport: Viewport = { themeColor: "#080d19", colorScheme: "dark" };

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${oxanium.variable} ${spaceGrotesk.variable} min-h-screen font-sans`}
      >
        <SiteFrame>{children}</SiteFrame>
      </body>
    </html>
  );
}

