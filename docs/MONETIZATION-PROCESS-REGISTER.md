# Registro de processos de monetização — AnderZilla

Documento vivo. Atualizar em toda criação, mudança de status ou encerramento de processo.
Agente responsável: `anderzilla-commerce-trust` (+ `anderzilla-commercial` para ofertas).
Skill: `anderzilla-trust-commerce` / `anderzilla-monetization`.

Legenda de status: `ideia` · `especificado` · `em_build` · `ativo` · `pausado` · `encerrado`  
Legenda Market: `br` · `intl` · `global` · `n/a`

| ID | Processo | Market | Onde no site | Como monetiza | Status | CMS? | Próxima ação | Atualizado |
|----|----------|--------|--------------|---------------|--------|------|--------------|------------|
| mon-forgekit | ForgeKit produto próprio | intl | /forgekit + Gumroad | US$149 one-time ZIP | ativo | sim (implementação local) | CMS/página PT+EN validados localmente; validar release Azure; venda Gumroad permanece ativa | 2026-09-17 |
| mon-hub-br | Hub comercial Área Brasil | br | /comercio/brasil | Agrupa ofertas BRL/afiliados BR | em_build | sim (implementação local) | Hub BR/estado vazio implementado e validado localmente; publicar e verificar Azure | 2026-09-17 |
| mon-hub-intl | Hub comercial Área Internacional | intl | /comercio/internacional | Agrupa ForgeKit + afiliados USD | em_build | sim (implementação local) | Hub INT/ForgeKit implementado e validado localmente; publicar e verificar Azure | 2026-09-17 |
| mon-stackpick | StackPick comparações | global | /stackpick | Afiliado quando aprovado (por market) | em_build | sim (implementação local) | CTAs por mercado implementado e validado localmente; afiliação depende de aprovação real | 2026-09-17 |
| mon-aff-br | Afiliados Brasil | br | /parceiros?market=br · hub BR | Amazon BR, ML, Hotmart… | em_build | sim (implementação local) | CMS por mercado preparado; nenhum candidato aprovado/ativado nesta execução | 2026-09-17 |
| mon-aff-intl | Afiliados Internacional | intl | /parceiros?market=intl · hub INT | SaaS/Impact/Awin… | em_build | sim (implementação local) | CMS por mercado preparado; nenhum candidato ativado; PartnerStack permanece pausado | 2026-09-17 |
| mon-ads | Slots publicidade | global | home / inventário | Ads / house | em_build | sim (implementação local) | Flags/vigência/placements implementados e validado localmente; nenhum anúncio vendido ou ativado | 2026-09-17 |
| mon-live | Lives Twitch/YT/Kick | global | #live / hub live | Tips, subs, sponsor in-stream | em_build | parcial | Cadência + disclosure live | 2026-09-10 |
| mon-sponsor | Patrocínios diretos | global | /patrocine | Pacotes fechados | em_build | sim (implementação local) | Página/pacotes PT+EN implementado e validado localmente; sem contrato ou outreach | 2026-09-17 |
| mon-newsletter | Lista email | global | captura hub | Sponsor / lançamentos | ideia | sim | Lead magnet real | 2026-09-10 |
| mon-tiktok-shop | TikTok Shop links (@anderzilla) | br | /loja-tiktok ou hub BR | Tráfego→TikTok Shop / comissão ETP se elegível | especificado | sim | Confirmar ETP na conta; MVP CMS com Copy Link; ver research/TIKTOK-SHOP-SITE-LINKS.md | 2026-09-17 |
| mon-auth-accounts | Contas leitor + e-mail/OAuth + perfil | global | /entrar /perfil | Habilita KP real e personalização sync | especificado | sim | Rodar BRIFs auth multi-IA (gap→legal→backend→UI) | 2026-09-17 |
| mon-karaca | Karaca Points / Store | global | #points #store | Retenção (não vende KP) | em_build (demo) | sim (flags) | Plano econômico/XP preparado; definir verba e coorte; auth+ledger antes de resgate | 2026-09-10 |
| mon-karaca-sponsored | Campanhas e catálogo Karaca patrocinados | global | Store Points + missões (proposto) | Conteúdo/campanha patrocinados; benefícios financiados | especificado | planejado | Negociar direito de resgate, cobertura, região e regulamento; nenhum sponsor ativo | 2026-09-10 |
| mon-karaca-supply | Fornecimento B2B de recompensas | global | Store Points (proposto) | Custo de operação/retencão; não receita automática | especificado | planejado | Cotar fornecedores BR e validar elegibilidade, mínimos e SKUs; sem compra autorizada | 2026-09-10 |
| mon-partnerstack | Rede PartnerStack | intl | — | SaaS affiliates USD | pausado | n/a | Reaplicar ≥ 2026-09-21 | 2026-09-10 |
| mon-kiwify-br | Infoproduto/checkout BRL | br | hub BR (futuro) | PIX → C6 via plataforma BR | ideia | sim | Avaliar Kiwify/Hotmart vs Stripe BR | 2026-09-10 |
| mon-trust | Trust / Transparência | global | /transparencia | Confiança (explica BR×INT) | em_build | sim (implementação local) | Trust PT+EN e BR×INT implementados e validado localmente; publicar e verificar Azure | 2026-09-17 |
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

## Execução Trust & Commerce — 17/09/2026

Prompt executado no código local, com CMS/Admin/publisher e superfícies PT/EN por mercado. `em_build` distingue capacidade de software de operação comercial publicada. Não houve deploy Azure, candidatura, contato com marcas, compra, anúncio real nem resgate KP. Validação final e roteiro de edição constam em `Z:/AnderZilla/docs/TRUST-COMMERCE-EDITOR-GUIDE.md`; inventário dos demais prompts em `Z:/AnderZilla/docs/PROMPT-EXECUTION-AUDIT.md`.

Leitura pública nesta data: Gumroad ForgeKit HTTP 200, preço estruturado USD 149,00; demo HTTP 200. Checkout, conteúdo do ZIP e payout não foram testados. Nenhuma evidência nova de parceiro ativo.
