import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Hub from "@/components/hub/Hub";

type Params = { lang: string };

export const dynamicParams = false;

export function generateStaticParams() {
  return [{ lang: "pt" }, { lang: "en" }];
}

function language(lang: string): "pt" | "en" {
  if (lang !== "pt" && lang !== "en") notFound();
  return lang;
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const lang = language((await params).lang);
  const pt = lang === "pt";
  return {
    title: pt ? "AnderZilla — Games, IA e boas descobertas" : "AnderZilla — Games, AI and good discoveries",
    description: pt
      ? "Explore games, IA, gadgets e curiosidades com o Ghost. Seu radar de descobertas, desafios, lives e Karaca Points."
      : "Explore games, AI, gadgets and curiosities with the Ghost. Your radar for discoveries, challenges, streams and Karaca Points.",
    alternates: {
      canonical: `/${lang}/`,
      languages: { "pt-BR": "/pt/", en: "/en/" },
    },
  };
}

export default async function LanguageHome({ params }: { params: Promise<Params> }) {
  const lang = language((await params).lang);
  return <Hub initialLang={lang} />;
}
