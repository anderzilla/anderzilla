# Registro de processos de monetização — AnderZilla

Documento vivo. Atualizar em toda criação, mudança de status ou encerramento de processo.
Agente responsável: `anderzilla-commerce-trust` (+ `anderzilla-commercial` para ofertas).
Skill: `anderzilla-trust-commerce` / `anderzilla-monetization`.

Legenda de status: `ideia` · `especificado` · `em_build` · `ativo` · `pausado` · `encerrado`  
Legenda Market: `br` · `intl` · `global` · `n/a`

| ID | Processo | Market | Onde no site | Como monetiza | Status | CMS? | Próxima ação | Atualizado |
|----|----------|--------|--------------|---------------|--------|------|--------------|------------|
| mon-forgekit | ForgeKit produto próprio | intl | /forgekit + Gumroad | US$149 one-time ZIP | ativo | parcial→CMS | Trust + página CMS-driven | 2026-09-10 |
| mon-hub-br | Hub comercial Área Brasil | br | /comercio/brasil | Agrupa ofertas BRL/afiliados BR | especificado | sim | Implementar hub + empty state | 2026-09-10 |
| mon-hub-intl | Hub comercial Área Internacional | intl | /comercio/internacional | Agrupa ForgeKit + afiliados USD | especificado | sim | Implementar hub + ForgeKit destaque | 2026-09-10 |
| mon-stackpick | StackPick comparações | global | /stackpick | Afiliado quando aprovado (por market) | especificado | sim | CTAs só active + market | 2026-09-10 |
| mon-aff-br | Afiliados Brasil | br | /parceiros?market=br · hub BR | Amazon BR, ML, Hotmart… | especificado | sim | Só aprovados + HTTPS | 2026-09-10 |
| mon-aff-intl | Afiliados Internacional | intl | /parceiros?market=intl · hub INT | SaaS/Impact/Awin… | especificado | sim | Só aprovados; PartnerStack pausado | 2026-09-10 |
| mon-ads | Slots publicidade | global | home / inventário | Ads / house | especificado | sim | Ocultar se não vendido | 2026-09-10 |
| mon-live | Lives Twitch/YT/Kick | global | #live / hub live | Tips, subs, sponsor in-stream | em_build | parcial | Cadência + disclosure live | 2026-09-10 |
| mon-sponsor | Patrocínios diretos | global | /patrocine | Pacotes fechados | especificado | sim | Kit sem métricas fake | 2026-09-10 |
| mon-newsletter | Lista email | global | captura hub | Sponsor / lançamentos | ideia | sim | Lead magnet real | 2026-09-10 |
| mon-karaca | Karaca Points / Store | global | #points #store | Retenção (não vende KP) | em_build (demo) | sim (flags) | Auth+ledger antes de resgate | 2026-09-10 |
| mon-partnerstack | Rede PartnerStack | intl | — | SaaS affiliates USD | pausado | n/a | Reaplicar ≥ 2026-09-21 | 2026-09-10 |
| mon-kiwify-br | Infoproduto/checkout BRL | br | hub BR (futuro) | PIX → C6 via plataforma BR | ideia | sim | Avaliar Kiwify/Hotmart vs Stripe BR | 2026-09-10 |
| mon-trust | Trust / Transparência | global | /transparencia | Confiança (explica BR×INT) | especificado | sim | Implementar com Commerce CMS | 2026-09-10 |
| mon-platform | Receita nativa YT/Twitch | global | canais | Ads plataforma / bits | ideia | n/a | Após cadência estável | 2026-09-10 |

## Rails de payout (operador — não publicar dados sensíveis)

- **USD / INT:** destino Wise (informado só no painel da plataforma). Gumroad seller BR hoje via PayPal quando aplicável.
- **BRL / BR:** destino C6 / PIX (informado só no painel). Nunca commit de chave PIX/CPF/conta.

## Como atualizar (obrigatório)

1. Mudou status, market ou surgiu processo → editar esta tabela no mesmo PR/commit de docs.  
2. Mudou IA de rotas/CMS → atualizar `TRUST-AND-COMMERCE-CMS.md`.  
3. Rodar skill `anderzilla-trust-commerce` no início de tarefas commerce.  
4. Nunca marcar afiliado/sponsor/`ativo` sem evidência (contrato + URL + market).  
5. Registrar data (America/Sao_Paulo) na coluna Atualizado.