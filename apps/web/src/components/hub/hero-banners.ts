/**
 * Banners manuais do carrossel da home.
 *
 * Eles giram no mesmo bloco das notícias e não ocupam as 5 vagas
 * (as cinco notícias mais novas; a mais antiga sai quando entra uma mais nova).
 * Notícias vêm primeiro; banners ativos entram em seguida, nesta ordem.
 *
 * O banner Karaca é o fallback. Ele só aparece quando não há notícia
 * nem outro banner manual ativo.
 *
 * Para adicionar um banner promocional, copie um objeto para `heroBanners`
 * e mantenha o Karaca na lista:
 *
 * {
 *   id: "campanha-exemplo",
 *   image: "/brand/caveira.webp", // arquivo original do kit; não redesenhe o logo
 *   width: 1536,
 *   height: 1024,
 *   imageAlt: { pt: "", en: "" },
 *   kicker: { pt: "ANDERZILLA", en: "ANDERZILLA" },
 *   kickerNote: { pt: "NOVIDADE", en: "NEW" },
 *   title: { pt: "Título do banner", en: "Banner title" },
 *   text: { pt: "Texto curto.", en: "Short text." },
 *   cta: { pt: "Ver oferta", en: "See the offer" },
 *   link: { pt: "/pt/produtos/", en: "/en/produtos/" },
 *   startsAt: "2026-11-01", // inclusive
 *   endsAt: "2026-11-07",   // inclusive
 * }
 *
 * Sem startsAt e endsAt, o banner fica ativo sempre.
 * Não use fallback: true — isso reserva o banner para o carrossel vazio.
 * A imagem precisa existir em apps/web/public.
 */
export type Localized = { pt: string; en: string };

export type ManualBanner = {
  id: string;
  image: string;
  width?: number;
  height?: number;
  imageAlt: Localized;
  kicker: Localized;
  kickerNote?: Localized;
  title: Localized;
  /** Trecho do título desenhado na cor de acento. */
  emphasis?: string;
  text: Localized;
  cta?: Localized;
  link?: Localized;
  /** Dia YYYY-MM-DD inclusive. Omita os dois para ficar sempre ativo. */
  startsAt?: string;
  endsAt?: string;
  /** Só entra quando não há notícia nem outro banner ativo. */
  fallback?: boolean;
};

export const karacaBanner: ManualBanner = {
  id: "karaca",
  image: "/brand/caveira.webp",
  width: 1536,
  height: 1024,
  imageAlt: { pt: "", en: "" },
  kicker: { pt: "ANDERZILLA", en: "ANDERZILLA" },
  kickerNote: { pt: "ABRA UMA NOVA FASE", en: "ENTER A NEW LEVEL" },
  title: { pt: "Seu próximo\n“Karaca!”\nestá aqui.", en: "Your next\n“Karaca!”\nstarts here." },
  emphasis: "“Karaca!”",
  text: {
    pt: "Uma corrida nova, um gadget improvável ou uma IA que resolve aquele perrengue. Escolha sua próxima descoberta.",
    en: "A new race, an unexpected gadget or AI that solves a little everyday problem. Pick your next discovery.",
  },
  fallback: true,
};

export const heroBanners: ManualBanner[] = [karacaBanner];
