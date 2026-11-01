import cmsPublished from './cms-published.json';
import discoveryData from "./discoveries.json";

export type Language = "pt" | "en";
export const categories = [
  "games",
  "consoles",
  "celulares",
  "ia",
  "gadgets",
  "curiosidades",
] as const;
export type Category = (typeof categories)[number];
export type Route =
  | "home"
  | "saved"
  | "quiz"
  | "profile"
  | "channels"
  | "sponsor"
  | "live"
  | "agenda"
  | "points"
  | "store";
export const routes: Route[] = [
  "home",
  "saved",
  "quiz",
  "profile",
  "channels",
  "sponsor",
  "live",
  "agenda",
  "points",
  "store",
];
export interface Discovery {
  id: string;
  category: Category;
  titlePT: string;
  titleEN: string;
  summaryPT: string;
  summaryEN: string;
  sourceName: string;
  url: string;
  published: string;
  observed: string;
  fact: string;
  factEN: string;
  slugPT?: string;
  slugEN?: string;
  seoTitlePT?: string;
  seoTitleEN?: string;
  seoDescriptionPT?: string;
  seoDescriptionEN?: string;
  author?: string;
  tags?: string;
  coverMediaId?: string;
  mediaIds?: string;
  isDemo?: boolean;
  sources?: {name:string;url:string;publishedAt?:string;note?:string}[];
  verifiedAt?: string;
  /** Selo "Atualizado em", separado da apuração original. */
  updatedAt?: string;
  eventDate?: string;
  editorialType?: string;
  hashtagsPT?: string;
  hashtagsEN?: string;
  socialInstagramPT?: string;
  socialInstagramEN?: string;
  socialFacebookPT?: string;
  socialFacebookEN?: string;
  socialWhatsappPT?: string;
  socialWhatsappEN?: string;
  socialMediaId?: string;
  /** Post ou reel público. Quando preenchido, a home prioriza a notícia no carrossel e a página mostra o link. */
  instagramUrl?: string;
}
const INSTAGRAM_POST = /^\/(?:[A-Za-z0-9._]+\/)?(?:p|reel|reels|tv)\/[A-Za-z0-9_-]+\/?$/;
/** URL https de um post ou reel em instagram.com. Qualquer outro valor fica de fora da página e da fila. */
export function instagramPostUrl(value?: string) {
  const raw = value?.trim();
  if (!raw) return "";
  try {
    const url = new URL(raw);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || url.username || url.password) return "";
    if (host !== "instagram.com" && host !== "www.instagram.com") return "";
    if (!INSTAGRAM_POST.test(url.pathname)) return "";
    return url.toString();
  } catch {
    return "";
  }
}
export const discoveries = (cmsPublished.enabled ? cmsPublished.discoveries : discoveryData) as Discovery[];
export function articleUrl(item:Discovery,lang:Language){return `/${lang}/radar/${(lang==='pt'?item.slugPT:item.slugEN)||item.id}/`}
function calendarDay(value?: string) {
  const day = (value || "").slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : "";
}
/**
 * Última atualização (apuração ou selo, a mais recente).
 * A publicação entra só quando não há nenhuma das duas.
 * Ordenação e texto do card usam este mesmo dia.
 */
export function radarCardDate(item: Discovery) {
  const published = calendarDay(item.published);
  const editorial = [calendarDay(item.updatedAt), calendarDay(item.verifiedAt)].filter(Boolean).sort().at(-1) || "";
  if (editorial) return { day: editorial, revised: Boolean(published) && editorial > published };
  return { day: published, revised: false };
}
export function radarRecency(item: Discovery) {
  return radarCardDate(item).day || "0000-00-00";
}
export function formatRadarDay(day: string, lang: Language) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return day;
  return new Intl.DateTimeFormat(lang === "pt" ? "pt-BR" : "en-US", {
    day: lang === "pt" ? "2-digit" : "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${day}T12:00:00Z`));
}
export function radarCardLabel(item: Discovery, lang: Language) {
  const { day, revised } = radarCardDate(item);
  const formatted = formatRadarDay(day, lang);
  return revised ? (lang === "pt" ? `Atualizado em ${formatted}` : `Updated ${formatted}`) : formatted;
}
/** Mais nova primeiro. Empate: publicação mais recente e, depois, o título. */
export function compareRadarNewestFirst(a: Discovery, b: Discovery) {
  const byRecent = radarRecency(b).localeCompare(radarRecency(a));
  if (byRecent) return byRecent;
  const byPublished = calendarDay(b.published).localeCompare(calendarDay(a.published));
  if (byPublished) return byPublished;
  return a.titlePT.localeCompare(b.titlePT, "pt");
}
export function publishedRadar(){
  return discoveries.filter(item=>!item.isDemo).sort(compareRadarNewestFirst);
}
export const colors: Record<Category, string> = {
  games: "#b39aff",
  consoles: "#ff939b",
  celulares: "#ffd0ad",
  ia: "#a6adff",
  gadgets: "#8ee8d6",
  curiosidades: "#acc8ff",
};
export const YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@anderzilla-tv" as const;
export const YOUTUBE_LIVE_URL = `${YOUTUBE_CHANNEL_URL}/live` as const;
export const LIVE_STATUS_URL =
  "https://anderzilla-live.anderzilla.workers.dev/status" as const;
export const LIVE_STATUS_POLL_MS = 60_000;
export const socials = [
  ["YouTube", YOUTUBE_CHANNEL_URL],
  ["Twitch", "https://www.twitch.tv/anderzillacwb"],
  ["TikTok", "https://www.tiktok.com/@anderzilla"],
  ["Instagram", "https://www.instagram.com/anderzilla/"],
  ["Kick", "https://kick.com/anderzilla"],
] as const;
export const pointRules = { quiz: 100, interests: 25 } as const;
export type Mission = keyof typeof pointRules;
export interface PlayerState {
  saved: string[];
  opened: string[];
  interests: Category[];
  quizDone: boolean;
  claims: Mission[];
}
export const freshPlayer = (): PlayerState => ({
  saved: [],
  opened: [],
  interests: [],
  quizDone: false,
  claims: [],
});
export function parsePlayer(value: unknown): PlayerState {
  const result = freshPlayer();
  if (!value || typeof value !== "object") return result;
  const raw = value as Record<string, unknown>;
  for (const field of ["saved", "opened"] as const)
    if (Array.isArray(raw[field]))
      result[field] = [
        ...new Set(
          raw[field].filter(
            (id): id is string =>
              typeof id === "string" && discoveries.some((x) => x.id === id),
          ),
        ),
      ];
  if (Array.isArray(raw.interests))
    result.interests = [
      ...new Set(
        raw.interests.filter((id): id is Category =>
          categories.includes(id as Category),
        ),
      ),
    ];
  if (Array.isArray(raw.claims))
    result.claims = [
      ...new Set(
        raw.claims.filter(
          (id): id is Mission => id === "quiz" || id === "interests",
        ),
      ),
    ];
  result.quizDone = raw.quizDone === true;
  return result;
}
export const platforms = {
  twitch: { name: "Twitch", url: "https://www.twitch.tv/anderzillacwb" },
  youtube: {
    name: "YouTube",
    url: YOUTUBE_CHANNEL_URL,
  },
  kick: { name: "Kick", url: "https://kick.com/anderzilla" },
};
export type Platform = keyof typeof platforms;
export interface HubEvent {
  url?: string;
  isDemo?: boolean;
  id: string;
  platform: Platform;
  titlePT: string;
  titleEN: string;
  startsAt: string;
}
export interface Broadcast {
  platform: Platform;
  title: string;
  checkedAt: string;
  expiresAt: string;
}
export interface LiveStatus {
  live: boolean;
  title: string;
  url: string;
  platform: "youtube";
  startedAt: string;
  updatedAt: string;
}
function httpsUrl(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 2000) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return null;
    return url.href;
  } catch {
    return null;
  }
}
export function parseLiveStatus(value: unknown): LiveStatus | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  if (typeof raw.live !== "boolean") return null;
  if (raw.platform !== "youtube") return null;
  return {
    live: raw.live,
    title: typeof raw.title === "string" ? raw.title.trim() : "",
    url: httpsUrl(raw.url) ?? YOUTUBE_LIVE_URL,
    platform: "youtube",
    startedAt: typeof raw.startedAt === "string" ? raw.startedAt : "",
    updatedAt: typeof raw.updatedAt === "string" ? raw.updatedAt : "",
  };
}
export interface Affiliate {
  isDemo?: boolean;
  titlePT: string;
  titleEN: string;
  url: string;
  status: "active" | "pending";
}
// Public editorial configuration only. Production wallet authority belongs in the API.
export const hubSettings: {
  events: HubEvent[];
  broadcast: Broadcast | null;
  youtubeVideoId: string | null;
  affiliates: Affiliate[];
} = { events: cmsPublished.events as HubEvent[], broadcast: null, youtubeVideoId: null, affiliates: cmsPublished.affiliates as Affiliate[] };
