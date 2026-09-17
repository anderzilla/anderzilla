# BRIEF A — Codex: Trust & Commerce + Áreas Brasil × Internacional

**Cole isto no Codex** com workspace `Z:\AnderZilla` (branch `codex/anderzilla-foundation`).
Prompt completo também em: `docs/TRUST-AND-COMMERCE-CMS-PROMPT.md` e `Z:\AnderZilla-docs\strategy\TRUST-AND-COMMERCE-CMS-PROMPT.md`.
Roteiro: `docs/ROTEIRO-TORNAR-REAL.md` · Fase 1.

## Contexto prod (2026-09-16)

- https://anderzilla.com/ no ar (200): hub editorial, ForgeKit, StackPick.
- ForgeKit US$149 → https://anderzilla.gumroad.com/l/edkel (sem Polar).
- Ainda **404**: `/pt/comercio/brasil`, `/pt/comercio/internacional`, `/pt/transparencia` (+ aliases EN).
- Afiliados BR: só candidatos (`docs/CANDIDATES-AFFILIATES-BR.md`) — **nenhum ativo**.
- PartnerStack pausado até ≥ 2026-09-21.
- Live: badge só com broadcast confirmado; KP = demo (ver `docs/BRIEF-trust-commerce-live-karaca.md`).

## Pedido

Implementar Trust & Commerce no hub (`apps/web`, estender CMS/admin/publisher existentes):

1. **Área Brasil** — `/[lang]/comercio/brasil` (alias EN ok)
2. **Área Internacional** — `/[lang]/comercio/internacional`
3. **Trust** — `/[lang]/transparencia` (explica BR×INT + ForgeKit + live/KP honestos)
4. Também: produtos, parceiros, patrocine conforme `TRUST-AND-COMMERCE-CMS.md`
5. Campo CMS `market`: `br` | `intl` | `global`; empty states honestos
6. ForgeKit CTA continua Gumroad edkel; sem Polar stub
7. Atualizar `docs/MONETIZATION-PROCESS-REGISTER.md` se status avançar
8. `npm run build` verde nas apps tocadas

## Não fazer

Outreach; inventar afiliados/métricas/parceiros; Polar; dados bancários/CPF/PIX no git; push Azure prod sem Anderson pedir (homolog visual ok se souber o script).

## Done when

Rotas BR/INT/Trust **200** local (e prontas pra deploy); Trust explica as duas áreas; empty states sem fingir parceiro; build verde; resumo de rotas/tipos CMS.