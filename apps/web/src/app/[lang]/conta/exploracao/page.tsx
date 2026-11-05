import type { Metadata } from "next";
import { MemberArea } from "@/components/account/MemberArea";
import {
  buildContaMetadata,
  validateContaLang,
  type ContaParams,
} from "../routeHelper";

export const dynamicParams = false;
export function generateStaticParams() {
  return [{ lang: "pt" }, { lang: "en" }];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<ContaParams>;
}): Promise<Metadata> {
  const { lang } = await params;
  return buildContaMetadata(
    lang,
    "exploracao",
    "Exploração e Passaporte",
    "Exploration & Passport",
  );
}

export default async function ContaExploracaoPage({
  params,
}: {
  params: Promise<ContaParams>;
}) {
  const { lang } = await params;
  return <MemberArea lang={validateContaLang(lang)} view="exploration" />;
}
