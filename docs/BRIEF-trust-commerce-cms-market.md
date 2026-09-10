# BRIEF B — Codex paralelo: CMS / Admin market (br | intl | global)

Rode em paralelo ao BRIEF principal (`docs/BRIEF-trust-commerce-br-intl.md`), idealmente em outra sessão Codex no mesmo monorepo `Z:\AnderZilla`.

## Escopo (só isto)
1. Estender `services/cms` + `apps/admin` + `services/publisher` para content types comerciais com campo obrigatório `market`: `br` | `intl` | `global`.
2. Tipos: products, affiliate_placements, ad_placements, sponsor_packages, trust_blocks, feature_flags, market_hubs (conforme strategy/TRUST-AND-COMMERCE-CMS.md nos docs).
3. Flags: showMarketBr, showMarketIntl, showAffiliatesBr, showAffiliatesIntl, showAds, showSponsor, showPointsStore.
4. Fluxo draft → preview → publish já existente; não criar sistema paralelo.
5. Snapshot publicado deve alimentar o hub sem inventar afiliados ativos.
6. Atualizar `docs/MONETIZATION-PROCESS-REGISTER.md` só se o status CMS avançar (ex.: mon-hub-br CMS? → sim).

## Fora
Rotas públicas Hub (ficam no BRIEF A); outreach; secrets bancários; deploy Azure.

## Done
Admin edita e publica por market; build admin/cms/publisher verde; resumo dos campos e passos do editor.