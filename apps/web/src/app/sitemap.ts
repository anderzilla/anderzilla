import {commerceRoutes} from "@/components/commerce/data";
import type { MetadataRoute } from "next";
import { SITE } from "../../content/affiliates";
import { listComparisons } from "../../content/stackpick";
import { articleUrl, publishedRadar } from '@/components/hub/model';

export const dynamic = "force-static";

function absolute(path: string) {
  const prefixed = path.startsWith("http") ? path : `${SITE.url}${path.startsWith("/") || path === "" ? path : `/${path}`}`;
  return prefixed.endsWith("/") ? prefixed : `${prefixed}/`;
}

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const base = [
    "",
    "/pt",
    "/en",
    "/forgekit",
    "/stackpick",
    "/about",
    "/links",
    "/privacy",
    "/terms",
  ];
  const comparisons = listComparisons().map((c) => `/stackpick/${c.slug}`);
  const radarIndexes:MetadataRoute.Sitemap=(['pt','en'] as const).map(lang=>({url:absolute(`/${lang}/radar`),lastModified:now,changeFrequency:'daily' as const,priority:0.8,alternates:{languages:{'pt-BR':absolute('/pt/radar'),en:absolute('/en/radar')}}}));
  const articles:MetadataRoute.Sitemap=publishedRadar().flatMap(item=>(['pt','en'] as const).map(lang=>({url:absolute(articleUrl(item,lang)),lastModified:item.updatedAt||item.verifiedAt||item.published,changeFrequency:'weekly' as const,priority:0.7,alternates:{languages:{'pt-BR':absolute(articleUrl(item,'pt')),en:absolute(articleUrl(item,'en'))}}})));
  const routes = [...base, ...comparisons, ...["pt","en"].flatMap(lang=>commerceRoutes.map(route=>`/${lang}/${route}`))];

  return [...routes.map((route) => ({
    url: absolute(route),
    lastModified: now,
    changeFrequency:
      route === "" || route === "/pt" || route === "/en" || route === "/forgekit" || route.startsWith("/stackpick")
        ? "weekly" as const
        : "monthly" as const,
    priority:
      route === "" || route === "/pt"
        ? 1
        : route === "/en" || route === "/forgekit"
          ? 0.9
          : route.startsWith("/stackpick")
            ? 0.8
            : 0.7,
  })),...radarIndexes,...articles];
}
