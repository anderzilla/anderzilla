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
}
export const discoveries = discoveryData as Discovery[];
export const colors: Record<Category, string> = {
  games: "#b39aff",
  consoles: "#ff939b",
  celulares: "#ffd0ad",
  ia: "#a6adff",
  gadgets: "#8ee8d6",
  curiosidades: "#acc8ff",
};
export const socials = [
  ["YouTube", "https://www.youtube.com/@anderzilla-tv"],
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
    url: "https://www.youtube.com/@anderzilla-tv/live",
  },
  kick: { name: "Kick", url: "https://kick.com/anderzilla" },
};
export type Platform = keyof typeof platforms;
export interface HubEvent {
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
export interface Affiliate {
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
} = { events: [], broadcast: null, youtubeVideoId: null, affiliates: [] };
