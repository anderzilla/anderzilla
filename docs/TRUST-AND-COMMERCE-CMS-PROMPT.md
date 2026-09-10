# PROMPT — Implementar Trust & Commerce CMS no hub AnderZilla

Cole no Codex (workspace `Z:\AnderZilla`) ou entregue ao agente `anderzilla-commerce-trust`.

---

You are working in Z:\AnderZilla (branch codex/anderzilla-foundation).
Canonical docs: Z:\AnderZilla-docs (branch codex/anderzilla-docs). Read AGENTS.md, strategy/TRUST-AND-COMMERCE-CMS.md, strategy/MONETIZATION-PROCESS-REGISTER.md, strategy/BRAND-AND-PRODUCT.md, strategy/HUB-LIVE-AND-MONETIZATION.md, strategy/SPONSOR-KIT-DRAFT.md, strategy/KARACA-POINTS.md, research/monetization.md, strategy/ADMIN-CMS-PLAN.md before coding.

## Goal
Build a coherent, organized, CMS-controllable Monetization / Trust area on the AnderZilla hub (apps/web) so current and next monetization strategies have real site backing and users feel safe buying, clicking affiliate links, watching sponsored lives, or engaging with Karaca Points.

Brand: AnderZilla. Languages: PT-BR + EN. No fake metrics, testimonials, partners, or active affiliates. Never use CodeMatrix cloud/creds.

## Product facts (verified)
- ForgeKit: one-time US$149 on Gumroad https://anderzilla.gumroad.com/l/edkel
- Delivery: ZIP + GETTING_STARTED on Gumroad
- Demo: https://forgekit-kwzn5potra-rj.a.run.app
- Buy CTA must go to Gumroad (not Polar stub)
- PartnerStack declined until 2026-09-21 — do not claim PartnerStack partnership
- Affiliates: only status=active AND verified HTTPS URL; empty = honest empty/official-source state
- Ad slots: hide or house-ad if not sold; never fake an advertiser
- Karaca Points: no cash purchase of points; no real redemptions until auth+API+stock — label demo vs production
- Azure SWA is primary hosting for the portal

## Build
1) Public Trust & Commerce hub routes (produtos, forgekit, stackpick, parceiros, patrocine, transparencia) with PT+EN
2) ForgeKit premium CMS-driven page with verified fallbacks; no Polar stub language
3) CMS + apps/admin types: products, affiliate_placements, ad_placements, sponsor_packages, trust_blocks, feature_flags; draft→preview→publish via existing publisher
4) Trust UX: disclosure near CTAs; honest empty states; points demo watermark if needed
5) Nav per BRAND-AND-PRODUCT; preserve redirects for /forgekit /stackpick

## Out of scope
No brand outreach emails; no real KP redemptions; no ad networks; no invented analytics; no Azure prod push unless asked.

## Success
Trust page explains money; ForgeKit complete; CMS can publish commerce content without code; inactive channels not fake; builds green; summarize routes, content types, editor publish steps.

Prefer extending existing cms/publisher. Incremental OK: (A) Trust+ForgeKit with snapshot fallbacks → (B) Admin fields → (C) Publisher snapshot.

After changes: update strategy/MONETIZATION-PROCESS-REGISTER.md statuses if implementation advances a process.