# Anderzilla

Personal brand hub for **Anderson Henrique Gonçalves** — products, StackPick, and geek fuel for programmers, gamers, and tech nerds.

**Site:** https://anderzilla.com · **Not** CodeMatrix.

## Stack

- Next.js 15 (App Router) + TypeScript
- Tailwind CSS
- `output: 'standalone'` for Cloud Run

## Local development

```bash
npm install
npm run dev
```

Open http://localhost:3000

Production build:

```bash
npm run build
npm start
```

Use your preferred Node package manager.

## Key routes

| Route | Purpose |
|-------|---------|
| `/` | Hero, audience, ForgeKit, StackPick teaser |
| `/forgekit` | Product page · Buy → Gumroad US$149 |
| `/stackpick` | pSEO hub + affiliate placeholders |
| `/about` | Anderson / Anderzilla |
| `/links` | Link-in-bio |
| `/privacy` `/terms` | Legal + affiliate disclosure |

## Monetization links

- **ForgeKit Buy:** https://anderzilla.gumroad.com/l/edkel
- **Live demo:** https://forgekit-kwzn5potra-rj.a.run.app
- **Affiliates:** `content/affiliates.ts` (`STACKPICK_TODO` placeholders only)

## DNS for anderzilla.com

1. Map the domain in Cloud Run (Manage custom domains) for `anderzilla.com` and `www`.
2. Add the DNS records Google shows (A/AAAA or CNAME + TXT verification).
3. Prefer HTTPS only; redirect www ↔ apex at the edge (e.g. Cloudflare).

## Deploy to Cloud Run

1. Keep `output: 'standalone'` in `next.config.ts`.
2. Multi-stage Dockerfile: install deps → build → copy `.next/standalone`, `.next/static`, `public` into a Node 20 image.
3. Expose port 8080; start with `node server.js`.
4. Example:

```bash
gcloud run deploy anderzilla --source . --region southamerica-east1 --allow-unauthenticated --port 8080
```

## SEO

- Metadata + Open Graph (`src/app/opengraph-image.tsx`)
- `src/app/sitemap.ts`, `src/app/robots.ts`

## License

Private / all rights reserved unless otherwise noted.
