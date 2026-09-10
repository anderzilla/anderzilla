# Trust & Commerce CMS — área de monetização no hub AnderZilla

**Status:** especificação viva (atualizar quando entrar/sair processo de monetização)  
**Código:** `Z:/AnderZilla` · branch típica `codex/anderzilla-foundation`  
**Docs:** `Z:/AnderZilla-docs` · branch `codex/anderzilla-docs`  
**Agentes:** `anderzilla-commercial`, `anderzilla-commerce-trust`  
**Skills:** `anderzilla-monetization`, `anderzilla-trust-commerce`

## Objetivo

Área coerente, organizada e **controlável pelo CMS** para ForgeKit e demais estratégias de monetização (atuais e próximas), com respaldo de site que dê **segurança ao usuário** (transparência, disclosure, estados vazios honestos).

## Duas áreas de mercado (obrigatório)

Separar sempre a monetização em **Área Brasil** e **Área Internacional**. Idioma do site (`pt`/`en`) ≠ mercado: um visitante PT pode ver ofertas INT e vice-versa, com rótulo claro de mercado/moeda/loja.

| Área | Moeda / payout (operador) | Comprador típico | Canais (status real) |
|------|---------------------------|------------------|----------------------|
| **Brasil** | BRL → C6 / PIX (painel da plataforma; sem dados bancários no Git) | BR | Amazon Associados BR, Mercado Livre, Hotmart/Monetizze/Kiwify (quando aprovados), Stripe BR/PIX futuro, AdSense BR, creators YT/TikTok BR, patrocínios locais |
| **Internacional** | USD → Wise (via rail da plataforma: Gumroad/PayPal etc.) | Global EN+ | ForgeKit Gumroad US$149 (ativo), PartnerStack (pausado até ≥2026-09-21), Amazon US, Fanatical/Awin, ElevenLabs, Hostinger, Logitech/Impact, Impact/SaaS, ads USD |

Regras:
- Todo placement CMS tem `market`: `br` | `intl` | `global`.
- CTAs mostram moeda e loja (ex.: “Comprar na Gumroad · USD”).
- Afiliado BR não mistura cookie/loja US no mesmo botão.
- Trust center explica as duas áreas e que imposto/payout do operador não é o mesmo do checkout do comprador.
- Nunca colar CPF, conta, PIX completo ou dados Wise no repositório.

## Fatos verificados (não inventar)

- ForgeKit US$149 · Gumroad https://anderzilla.gumroad.com/l/edkel · ZIP + GETTING_STARTED · market=`intl`
- Demo https://forgekit-kwzn5potra-rj.a.run.app · Buy → Gumroad (não Polar stub)
- PartnerStack declined até 2026-09-21
- Afiliados: só `active` + URL HTTPS verificada + `market` preenchido
- Ads: slot não vendido → ocultar ou house ad; nunca anunciante fictício
- Karaca Points: retenção; sem venda de pontos; `market=global` / flags
- Azure SWA = hosting portal; marca AnderZilla; PT-BR + EN

## Rotas públicas alvo

| Rota (conceito) | Função |
|---|---|
| `/[lang]/produtos` | Catálogo (filtros BR / INT / todos) |
| `/[lang]/forgekit` | ForgeKit premium (área INT) |
| `/[lang]/comercio/brasil` | Hub comercial Área Brasil |
| `/[lang]/comercio/internacional` | Hub comercial Área Internacional |
| `/[lang]/stackpick` | Comparações (ranking editorial ≠ receita; CTA por market) |
| `/[lang]/parceiros` | Afiliados/parceiros + disclosure + filtro market |
| `/[lang]/patrocine` | Pacotes sponsor (sem métricas inventadas) |
| `/[lang]/transparencia` | Trust center (como ganhamos dinheiro · BR × INT) |

Aliases EN aceitáveis: `/en/commerce/brazil`, `/en/commerce/international` (redirect ou rotas paralelas).

## Modelo CMS

Extensão Karaca proposta em 10/09/2026, ainda não implementada: [plano de economia e operação](KARACA-ECONOMY-AND-PARTNERSHIPS.md). Acrescenta XP, temporadas, contratos de distribuição, lotes de recompensas, orçamento e revisão de resgates. Mantém `market`, separa aprovação de afiliado de autorização de troca por pontos e só publica SKU com direito, cobertura e entrega confirmados. Rotas `/[lang]/karaca` e `/[lang]/store-points` são alvos de planejamento; #points/#store atuais seguem demonstrativos.

Tipos: `products`, `affiliate_placements`, `ad_placements`, `sponsor_packages`, `trust_blocks`, `feature_flags`, `market_hubs`.  
Campos críticos: `market`, `currency`, `status`, `ctaUrl`, `disclosureKey`.  
Flags: showProducts, showAffiliatesBr, showAffiliatesIntl, showAds, showSponsor, showPointsStore, showMarketBr, showMarketIntl.  
Fluxo: draft → preview → published snapshot. Sem segredos no Git.

## Critérios de sucesso

1. Trust page explica BR × INT e a oferta ForgeKit  
2. Hubs `/comercio/brasil` e `/comercio/internacional` distintos, honestos se vazios  
3. ForgeKit completo, AnderZilla, CTA Gumroad USD  
4. Admin publica por market sem código  
5. Canais inativos não parecem quebrados/falsos  
6. PT-BR + EN  
7. Builds verdes + resumo de rotas/tipos

## Manutenção

Sempre que um processo for criado/alterado/encerrado: atualizar `MONETIZATION-PROCESS-REGISTER.md` (coluna Market) + este arquivo se a IA de rotas/CMS mudar + skill `anderzilla-trust-commerce`.
