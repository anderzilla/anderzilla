# PROMPT — Implementar Trust & Commerce CMS (com Áreas Brasil × Internacional)

Cole no Codex (workspace `Z:\AnderZilla`) ou entregue ao agente `anderzilla-commerce-trust` / Cloud Agent.

---

You are working in Z:\AnderZilla (branch codex/anderzilla-foundation).
Canonical docs: Z:\AnderZilla-docs (branch codex/anderzilla-docs). BEFORE coding, read:
- strategy/TRUST-AND-COMMERCE-CMS.md
- strategy/MONETIZATION-PROCESS-REGISTER.md
- strategy/BRAND-AND-PRODUCT.md
- strategy/HUB-LIVE-AND-MONETIZATION.md
- strategy/SPONSOR-KIT-DRAFT.md
- strategy/KARACA-POINTS.md
- research/monetization.md
- strategy/ADMIN-CMS-PLAN.md
- AGENTS.md

## Goal
Build a coherent, CMS-controllable Monetization / Trust area on the AnderZilla hub (apps/web) with an explicit split:

### Área Brasil (market=br)
- Currency narrative: BRL; operator payout rail C6/PIX (never put bank details in repo)
- Candidate channels only when approved: Amazon Associados BR, Mercado Livre, Hotmart/Monetizze/Kiwify, future Stripe BR/PIX products, local sponsors, BR creator programs
- Honest empty states if no active placements

### Área Internacional (market=intl)
- Currency narrative: USD; operator payout via platform rails toward Wise (Gumroad currently PayPal for BR seller — do not invent bank copy)
- Active today: ForgeKit on Gumroad https://anderzilla.gumroad.com/l/edkel US$149 + demo https://forgekit-kwzn5potra-rj.a.run.app
- PartnerStack paused until >= 2026-09-21 — do not claim partnership
- Candidates: Amazon US, Fanatical/Awin, ElevenLabs, Hostinger, Logitech/Impact, other SaaS affiliates when active

Lang (pt/en) is independent of market. Label every commercial CTA with market + currency + store.

## Build
1) Public routes: produtos, forgekit, comercio/brasil, comercio/internacional (EN aliases ok), stackpick, parceiros, patrocine, transparencia — PT+EN
2) Trust center explains how money works for BR vs INT; disclosure near CTAs
3) ForgeKit page premium CMS-driven with verified Gumroad CTA (no Polar stub marketing)
4) Extend CMS + apps/admin: products, affiliate_placements, ad_placements, sponsor_packages, trust_blocks, feature_flags, market_hubs — each with market field; draft→preview→publish via existing publisher
5) Nav per BRAND-AND-PRODUCT; preserve redirects for /forgekit /stackpick
6) Update MONETIZATION-PROCESS-REGISTER.md statuses/markets if implementation advances a process

## Out of scope
No brand outreach; no real KP cash redemptions; no ad networks install; no invented analytics/partners; no Azure prod push unless asked; no CPF/bank/PIX secrets in git.

## Success
- Distinct BR and INT commerce hubs
- Trust page explains both + ForgeKit
- Inactive channels honest
- CMS can publish per-market without code
- Builds green; summarize routes, content types, editor publish steps

Prefer extending existing cms/publisher/hub. Incremental OK: (A) Trust + market hubs + ForgeKit fallbacks → (B) Admin fields → (C) Publisher snapshot.