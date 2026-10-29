import {
  compareRadarNewestFirst,
  formatRadarDay,
  instagramPostUrl,
  radarCardDate,
  radarRecency,
  type Discovery,
  type Language,
} from "./model";
import { heroBanners, karacaBanner, type ManualBanner } from "./hero-banners";

/** Uma vaga por dia, nos últimos 5 dias. A mais antiga sai quando entra um dia novo. */
export const NEWS_SLOT_COUNT = 5;

export type NewsHeroSlide = { kind: "news"; item: Discovery };
export type ManualHeroSlide = { kind: "manual"; banner: ManualBanner };
export type HeroSlide = NewsHeroSlide | ManualHeroSlide;

export function shiftUtcDay(day: string, delta: number) {
  const date = new Date(`${day}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + delta);
  return date.toISOString().slice(0, 10);
}

function isDay(value: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function bannerIsActive(banner: ManualBanner, today: string) {
  if (banner.startsAt && today < banner.startsAt) return false;
  if (banner.endsAt && today > banner.endsAt) return false;
  return true;
}

/**
 * Fila de notícias do carrossel.
 * Janela: os últimos 5 dias civis, pela mesma data dos cards.
 * Uma notícia por dia, a mais recente daquele dia.
 * Se alguma da janela tem instagramUrl válido, só essas entram.
 * Caso contrário, entra a notícia de cada dia da janela.
 */
export function selectNewsForCarousel(items: Discovery[], today: string) {
  if (!isDay(today)) return [];
  const start = shiftUtcDay(today, -(NEWS_SLOT_COUNT - 1));
  const windowed = items.filter((item) => {
    if (item.isDemo) return false;
    const day = radarRecency(item);
    return day >= start && day <= today;
  });
  const social = windowed.filter((item) => instagramPostUrl(item.instagramUrl));
  const pool = social.length ? social : windowed;
  const byDay = new Map<string, Discovery>();
  for (const item of [...pool].sort(compareRadarNewestFirst)) {
    const day = radarRecency(item);
    if (!byDay.has(day)) byDay.set(day, item);
  }
  return [...byDay.keys()]
    .sort((a, b) => b.localeCompare(a))
    .slice(0, NEWS_SLOT_COUNT)
    .map((day) => byDay.get(day)!);
}

export function heroUpdatedLabel(item: Discovery, lang: Language) {
  const day = radarCardDate(item).day;
  if (!day) return "";
  const formatted = formatRadarDay(day, lang);
  return lang === "pt" ? `Atualizado em ${formatted}` : `Updated ${formatted}`;
}

export function buildHeroSlides(
  items: Discovery[],
  today: string,
  banners: ManualBanner[] = heroBanners,
): HeroSlide[] {
  const fallback = banners.find((banner) => banner.fallback) ?? karacaBanner;
  if (!isDay(today)) return [{ kind: "manual", banner: fallback }];
  const news: HeroSlide[] = selectNewsForCarousel(items, today).map((item) => ({ kind: "news", item }));
  const manuals: HeroSlide[] = banners
    .filter((banner) => !banner.fallback && bannerIsActive(banner, today))
    .map((banner) => ({ kind: "manual", banner }));
  if (news.length || manuals.length) return [...news, ...manuals];
  if (!bannerIsActive(fallback, today)) return [{ kind: "manual", banner: karacaBanner }];
  return [{ kind: "manual", banner: fallback }];
}
