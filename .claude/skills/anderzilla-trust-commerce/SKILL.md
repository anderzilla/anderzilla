---
name: anderzilla-trust-commerce
description: Use when implementing or updating AnderZilla Trust & Commerce pages, CMS commerce content types, monetization process register, ForgeKit storefront trust, affiliates/ads/sponsor empty-vs-active rules.
---

# anderzilla-trust-commerce

Documentação canônica: `Z:/AnderZilla-docs` branch `codex/anderzilla-docs`.

## Antes de qualquer mudança
1. Ler strategy/TRUST-AND-COMMERCE-CMS.md e strategy/MONETIZATION-PROCESS-REGISTER.md
2. Confirmar status real de cada processo (não promover candidato a ativo)
3. Usar strategy/TRUST-AND-COMMERCE-CMS-PROMPT.md como checklist de implementação

## Regras
- Trust center e disclosures perto de CTAs comerciais
- ForgeKit: Gumroad https://anderzilla.gumroad.com/l/edkel + demo Cloud Run; sem linguagem Polar stub
- Afiliados/ads/sponsor: estados vazios honestos; feature flags
- Karaca Points: não misturar com checkout em dinheiro
- Atualizar o registro de processos no mesmo trabalho
- Não enviar outreach a marcas sem autorização explícita

## Depois
npm run build nas apps tocadas; listar rotas e campos CMS novos; apontar como o admin publica.