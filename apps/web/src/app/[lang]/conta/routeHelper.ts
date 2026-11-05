import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { Language } from "@/components/hub/model";

export type ContaParams = { lang: string };

export function validateContaLang(lang: string): Language {
  if (lang !== "pt" && lang !== "en") notFound();
  return lang;
}

export function buildContaMetadata(
  lang: string,
  subpath: string,
  titlePT: string,
  titleEN: string,
): Metadata {
  const validLang = validateContaLang(lang);
  const pt = validLang === "pt";
  const title = pt ? titlePT : titleEN;
  const description = pt
    ? "Área autenticada do jogador AnderZilla."
    : "AnderZilla authenticated player area.";
  const suffix = subpath ? `/${subpath}/` : "/";
  return {
    title,
    description,
    robots: {
      index: false,
      follow: false,
      nocache: true,
    },
    alternates: {
      canonical: `/${validLang}/conta${suffix}`,
      languages: {
        "pt-BR": `/pt/conta${suffix}`,
        en: `/en/conta${suffix}`,
      },
    },
  };
}
