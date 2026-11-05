import type { Metadata } from "next";
import { MemberArea } from "@/components/account/MemberArea";
import { buildContaMetadata, validateContaLang } from "../../routeHelper";

type MissionParams = { lang: string; id: string };

const KNOWN_MISSION_IDS = [
  "detalhe",
  "checkpoint-curiosidade",
  "monte-seu-radar",
  "radar-ia-2026",
];

export const dynamicParams = false;
export function generateStaticParams() {
  return ["pt", "en"].flatMap((lang) =>
    KNOWN_MISSION_IDS.map((id) => ({ lang, id })),
  );
}

export async function generateMetadata({
  params,
}: {
  params: Promise<MissionParams>;
}): Promise<Metadata> {
  const { lang, id } = await params;
  return buildContaMetadata(
    lang,
    `missoes/${encodeURIComponent(id)}`,
    "Missão oficial",
    "Official mission",
  );
}

export default async function ContaMissaoDetailPage({
  params,
}: {
  params: Promise<MissionParams>;
}) {
  const { lang, id } = await params;
  return (
    <MemberArea
      lang={validateContaLang(lang)}
      view="mission_detail"
      missionId={id}
    />
  );
}
