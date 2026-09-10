import type { MetadataRoute } from "next";
import { SITE } from "../../content/affiliates";
import { listComparisons } from "../../content/stackpick";
import { discoveries, articleUrl } from '@/components/hub/model';

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const base = [
    "",
    "/forgekit",
    "/stackpick",
    "/about",
    "/links",
    "/privacy",
    "/terms",
  ];
  const comparisons = listComparisons().map((c) => `/stackpick/${c.slug}`);
  const articles=discoveries.filter(item=>!item.isDemo).flatMap(item=>[articleUrl(item,'pt'),articleUrl(item,'en')]);
  const routes = [...base, ...comparisons,...articles];

  return routes.map((route) => ({
    url: `${SITE.url}${route}`,
    lastModified: now,
    changeFrequency:
      route === "" || route === "/forgekit" || route.startsWith("/stackpick")
        ? "weekly"
        : "monthly",
    priority:
      route === ""
        ? 1
        : route === "/forgekit"
          ? 0.9
          : route.startsWith("/stackpick")
            ? 0.8
            : 0.7,
  }));
}
