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
| mon-aff-br | Afiliados Brasil | br | /parceiros?market=br · hub BR | Amazon BR, ML, Hotmart… | especificado | sim | Candidatos listados abaixo; só promover com aprovação+URL | 2026-09-10 |
| mon-aff-intl | Afiliados Internacional | intl | /parceiros?market=intl · hub INT | SaaS/Impact/Awin… | especificado | sim | Só aprovados; PartnerStack pausado | 2026-09-10 |
| mon-ads | Slots publicidade | global | home / inventário | Ads / house | especificado | sim | Ocultar se não vendido | 2026-09-10 |
| mon-live | Lives Twitch/YT/Kick | global | #live / hub live | Tips, subs, sponsor in-stream | em_build | parcial | Cadência + disclosure live | 2026-09-10 |
| mon-sponsor | Patrocínios diretos | global | /patrocine | Pacotes fechados | especificado | sim | Kit sem métricas fake | 2026-09-10 |
| mon-newsletter | Lista email | global | captura hub | Sponsor / lançamentos | ideia | sim | Lead magnet real | 2026-09-10 |
| mon-karaca | Karaca Points / Store | global | #points #store | Retenção (não vende KP) | em_build (demo) | sim (flags) | Plano econômico/XP preparado; definir verba e coorte; auth+ledger antes de resgate | 2026-09-10 |
| mon-karaca-sponsored | Campanhas e catálogo Karaca patrocinados | global | Store Points + missões (proposto) | Conteúdo/campanha patrocinados; benefícios financiados | especificado | planejado | Negociar direito de resgate, cobertura, região e regulamento; nenhum sponsor ativo | 2026-09-10 |
| mon-karaca-supply | Fornecimento B2B de recompensas | global | Store Points (proposto) | Custo de operação/retencão; não receita automática | especificado | planejado | Cotar fornecedores BR e validar elegibilidade, mínimos e SKUs; sem compra autorizada | 2026-09-10 |
| mon-partnerstack | Rede PartnerStack | intl | — | SaaS affiliates USD | pausado | n/a | Reaplicar ≥ 2026-09-21 | 2026-09-10 |
| mon-kiwify-br | Infoproduto/checkout BRL | br | hub BR (futuro) | PIX → C6 via plataforma BR | ideia | sim | Avaliar Kiwify/Hotmart vs Stripe BR | 2026-09-10 |
| mon-trust | Trust / Transparência | global | /transparencia | Confiança (explica BR×INT) | especificado | sim | Implementar com Commerce CMS | 2026-09-10 |
| mon-platform | Receita nativa YT/Twitch | global | canais | Ads plataforma / bits | ideia | n/a | Após cadência estável | 2026-09-10 |
| mon-automation-control | Controle de processos comerciais | global | CMS / Automações | Apoia verificação de ofertas e relatórios sem representar receita | em_build | sim | Painel/backend construídos e schema homolog aplicado; implantar bundle único e conectar fontes reais depois | 2026-09-10 |

## Planejamento Karaca! — 10/09/2026

[Plano de economia, gamificação e operação](KARACA-ECONOMY-AND-PARTNERSHIPS.md) e [diretório de candidatos/fontes](../research/KARACA-PARTNER-MAP-2026-09.md). XP separado de KP é proposta; KP continua sem venda/saque. ExitLag, Nuuvem, Fanatical, fornecedores de PIN e lojas são candidatos, não acordos ativos. Afiliado, fornecedor e patrocinador têm permissões distintas. Nenhum contato, cadastro, compra ou lançamento nesta pesquisa.

## Rails de payout (operador — não publicar dados sensíveis)

- **USD / INT:** destino Wise (informado só no painel da plataforma). Gumroad seller BR hoje via PayPal quando aplicável.
- **BRL / BR:** destino C6 / PIX (informado só no painel). Nunca commit de chave PIX/CPF/conta.

## Como atualizar (obrigatório)

1. Mudou status, market ou surgiu processo → editar esta tabela no mesmo PR/commit de docs.  
2. Mudou IA de rotas/CMS → atualizar `TRUST-AND-COMMERCE-CMS.md`.  
3. Rodar skill `anderzilla-trust-commerce` no início de tarefas commerce.  
4. Nunca marcar afiliado/sponsor/`ativo` sem evidência (contrato + URL + market).  
5. Registrar data (America/Sao_Paulo) na coluna Atualizado.

## Candidatos Área Brasil (afiliados / checkouts BRL)

Fonte: Caça Promo · 2026-09-10. **Nenhum `ativo`.** Só candidatura/docs oficiais — aprovação e URL de tracking ainda pendentes.

| ID | Candidato | URL oficial | Status | Notas |
|----|-----------|-------------|--------|-------|
| cand-amazon-br | Amazon Associados Brasil | https://associados.amazon.com.br/ | especificado | Programa oficial Amazon.com.br |
| cand-ml-br | Mercado Livre Afiliados/Criadores | https://www.mercadolivre.com.br/l/comece-a-recomendar | especificado | Links/IDs e campanhas creators ML BR |
| cand-hotmart | Hotmart Afiliados | https://signup.hotmart.com/pt-br/afiliado | especificado | Cadastro oficial afiliados |
| cand-monetizze | Monetizze Afiliados | https://www.monetizze.com.br/afiliados/ | especificado | Checkout BRL + vitrine |
| cand-kiwify | Kiwify Afiliados | https://ajuda.kiwify.com.br/pt-br/category/afiliados-18psomu/ | especificado | Docs; site https://kiwify.com.br/ |
| cand-magalu | Influenciador Magalu | https://www.parceiromagalu.com.br/divulgador | especificado | Programa Magalu PF |
| cand-shopee | Shopee Afiliados BR | https://affiliate.shopee.com.br/ | especificado | Portal + blog guia Shopee |
| cand-awin-br | Awin Brasil | https://ui.awin.com/publisher-signup/br/step1 | especificado | Rede publisher BR (KaBuM via Awin) |
| cand-lomadee | Lomadee | https://www.lomadee.com.br/pt-br/afiliados | especificado | Rede BR afiliados/creators |
| cand-afilio | Afilio | https://afilio.com.br/afiliados/ | especificado | Register: dashboard.afilio.com.br |
| cand-kabum | KaBuM! Afiliados | https://www.kabum.com.br/hotsite/afiliados/ | especificado | Oficial via Awin |
| cand-terabyte | Terabyte Parceiros | https://landing.terabyteshop.com.br/parceiros | especificado | Criadores tech/gamer |
| cand-eduzz | Eduzz | https://ajuda.eduzz.com/hc/pt-br/articles/4407884619547-como-fazer-para-me-cadastrar-na-eduzz | especificado | Parceiro via eduzz.com |
| cand-braip | Braip Afiliados | https://braip.com/afiliado | especificado | Landing oficial afiliado |
| cand-pichau | Pichau Parceiros | https://www.pichau.com.br/parceiros | ideia | Só lista influenciadores; inscrição afiliado pouco clara |

Regra: promover a `ativo` no processo `mon-aff-br` só com contrato/aprovação + URL HTTPS de tracking verificada + `market=br` no CMS.
