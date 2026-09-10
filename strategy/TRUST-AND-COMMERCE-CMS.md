# Trust & Commerce CMS — área de monetização no hub AnderZilla

**Status:** especificação viva (atualizar quando entrar/sair processo de monetização)  
**Código:** `Z:/AnderZilla` · branch típica `codex/anderzilla-foundation`  
**Docs:** `Z:/AnderZilla-docs` · branch `codex/anderzilla-docs`  
**Agentes:** `anderzilla-commercial`, `anderzilla-commerce-trust`  
**Skills:** `anderzilla-monetization`, `anderzilla-trust-commerce`

## Objetivo

Área coerente, organizada e **controlável pelo CMS** para ForgeKit e demais estratégias de monetização (atuais e próximas), com respaldo de site que dê **segurança ao usuário** (transparência, disclosure, estados vazios honestos).

## Fatos verificados (não inventar)

- ForgeKit US$149 · Gumroad https://anderzilla.gumroad.com/l/edkel · ZIP + GETTING_STARTED
- Demo https://forgekit-kwzn5potra-rj.a.run.app · Buy → Gumroad (não Polar stub)
- PartnerStack declined até 2026-09-21
- Afiliados: só `active` + URL HTTPS verificada; senão estado honesto / fonte oficial sem comissão
- Ads: slot não vendido → ocultar ou house ad; nunca anunciante fictício
- Karaca Points: sem venda de pontos; resgate real só com auth+API+estoque; demo rotulada
- Azure SWA = hosting portal; não herdar CodeMatrix; marca AnderZilla; PT-BR + EN

## Rotas públicas alvo

| Rota (conceito) | Função |
|---|---|
| `/[lang]/produtos` | Catálogo de produtos próprios |
| `/[lang]/forgekit` | Página ForgeKit premium CMS-driven |
| `/[lang]/stackpick` | Comparações (ranking editorial ≠ receita) |
| `/[lang]/parceiros` | Afiliados/parceiros + disclosure |
| `/[lang]/patrocine` | Pacotes sponsor (sem métricas inventadas) |
| `/[lang]/transparencia` | Trust center (como ganhamos dinheiro) |

Trust center cobre: quem é AnderZilla; como monetiza; disclosure; o que são/não são Karaca Points; compra ForgeKit; suporte; privacy/terms.

## Modelo CMS (controlável sem deploy)

Tipos: `products`, `affiliate_placements`, `ad_placements`, `sponsor_packages`, `trust_blocks`, `feature_flags`.  
Flags: showProducts, showAffiliates, showAds, showSponsor, showPointsStore.  
Fluxo: draft → preview → published snapshot (publisher existente). Sem segredos no Git.

## Critérios de sucesso

1. Trust page sozinha explica oferta e dinheiro  
2. ForgeKit completo, AnderZilla, CTA Gumroad  
3. Admin publica produto/afiliado/ad/sponsor/trust sem código  
4. Canais inativos não parecem quebrados/falsos  
5. PT-BR + EN nas rotas commerce/trust  
6. Builds verdes + resumo de rotas/tipos

## Prompt de implementação (Codex / agentes)

Ver seção completa em `strategy/TRUST-AND-COMMERCE-CMS-PROMPT.md` (mesmo conteúdo operacional expandido). Ao implementar: ler BRAND-AND-PRODUCT, HUB-LIVE-AND-MONETIZATION, SPONSOR-KIT-DRAFT, KARACA-POINTS, ADMIN-CMS-PLAN, research/monetization.md, MONETIZATION-PROCESS-REGISTER.md.

## Manutenção

Sempre que um processo de monetização for criado, alterado ou encerrado: atualizar `MONETIZATION-PROCESS-REGISTER.md` e, se mudar IA/CMS, este arquivo + skill `anderzilla-trust-commerce`.