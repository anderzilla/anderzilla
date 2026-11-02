import {
  compareRadarNewestFirst,
  formatRadarDay,
  radarCardDate,
  radarRecency,
  type Discovery,
  type Language,
} from "./model";
import { heroBanners, karacaBanner, type ManualBanner } from "./hero-banners";

/** Cinco notícias, da mais nova para a mais antiga. A mais antiga sai quando entra uma mais nova. */
export const NEWS_SLOT_COUNT = 5;

export type NewsHeroSlide = { kind: "news"; item: Discovery };
export type ManualHeroSlide = { kind: "manual"; banner: ManualBanner };
export type HeroSlide = NewsHeroSlide | ManualHeroSlide;

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
 * Cinco vagas, pela mesma data dos cards, da mais nova para a mais antiga.
 * Notas do mesmo dia entram juntas, na ordem do título, até fechar as vagas.
 */
export function selectNewsForCarousel(items: Discovery[], today: string) {
  if (!isDay(today)) return [];
  return items
    .filter((item) => !item.isDemo && radarRecency(item) <= today)
    .sort(compareRadarNewestFirst)
    .slice(0, NEWS_SLOT_COUNT);
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
