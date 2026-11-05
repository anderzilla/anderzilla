import type { MetadataRoute } from "next";
import { SITE } from "../../content/affiliates";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/pt/conta/", "/en/conta/", "/account/", "/account/callback/"],
    },
    sitemap: `${SITE.url}/sitemap.xml`,
  };
}
