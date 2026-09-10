# ForgeKit

Sellable Next.js digital product MVP for [Polar.sh](https://polar.sh) — **US$149** one-time.

Built by **Anderson Henrique Gonçalves** (Brazil). Personal indie brand — not CodeMatrix.

## What you get

- Marketing landing at `/` (hero, features, included list, price, FAQ)
- Auth: email/password sessions + `DEMO_MODE` for local unlock
- Prisma + SQLite: `User` and `Entitlement` models
- Polar stubs: `/api/checkout` and `/api/webhooks/polar`
- Gated `/dashboard` shell

## Quick start

```bash
cd forgekit
cp .env.example .env
npm install --legacy-peer-deps
npm run db:push
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

With `DEMO_MODE=true` (default), `/dashboard` is unlocked without login.

Production-style auth:

1. Set `DEMO_MODE=false`
2. Set a strong `AUTH_SECRET`
3. Register at `/login`

## Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Next.js dev server |
| `npm run build` | `prisma generate` + `next build` |
| `npm run start` | Start production server |
| `npm run db:push` | Push Prisma schema to SQLite |
| `npm run db:generate` | Generate Prisma Client |

> If installs fail on peer deps, use `npm install --legacy-peer-deps`.

## Environment

See `.env.example`:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLite path, e.g. `file:./dev.db` |
| `AUTH_SECRET` | Signs session cookies |
| `DEMO_MODE` | `true` unlocks dashboard without auth |
| `POLAR_ACCESS_TOKEN` | Polar organization access token |
| `POLAR_WEBHOOK_SECRET` | Webhook signing secret |
| `POLAR_PRODUCT_ID` | Product ID for the US$149 offering |
| `NEXT_PUBLIC_APP_URL` | App origin for redirects |

## Wire Polar (live keys)

1. Create a **one-time** product priced **US$149** in the Polar dashboard.
2. Copy the **Product ID** → `POLAR_PRODUCT_ID`.
3. Create an **organization access token** → `POLAR_ACCESS_TOKEN`.
4. Add a webhook to `https://YOUR_DOMAIN/api/webhooks/polar` → `POLAR_WEBHOOK_SECRET`.
5. Open `src/lib/polar.ts` and uncomment the `TODO:POLAR` fetch blocks for checkout creation and HMAC verification.
6. Adjust field mapping in `src/app/api/webhooks/polar/route.ts` to match Polar live event payloads.
7. Test: POST `/api/checkout` → redirect to Polar hosted checkout → webhook grants an `Entitlement`.

Checkout contract (stub or live):

```http
POST /api/checkout
Content-Type: application/json

{ "email": "buyer@example.com" }
```

Response: `{ "url", "id", "mode": "stub"|"live", "configured": boolean }`.

## License note for buyers

You receive a **perpetual license** to use and modify ForgeKit in personal and commercial projects.

You may **not**:

- Resell the unmodified starter as a competing template or digital product
- Share the raw source publicly as a free clone of ForgeKit

Attribution appreciated but not required.

## Stack

- Next.js (App Router) · React · TypeScript · Tailwind CSS v4
- Prisma · SQLite (demo) · bcryptjs sessions
- Polar.sh checkout/webhook stubs

## Owner

Anderson Henrique Gonçalves — indie builder, Brazil.
