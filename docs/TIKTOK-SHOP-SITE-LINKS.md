# TikTok Shop no site AnderZilla — links (sem checkout no hub)

**Data:** 2026-09-17 · Pesquisa documental (Seller Academy / Partner Center / fontes BR).  
**Conta alvo:** TikTok `@anderzilla`  
**Objetivo do Anderson:** sessão no hub com produtos da TikTok Shop — **não vender no site**, só links para a loja / afiliados.

## Resposta curta

**Sim, é viável** como vitrine de **links de saída** (product / showcase / shop page), com disclosure.  
**Não** há (para o nosso caso) um “widget embed oficial” que venda dentro do anderzilla.com — a compra continua no TikTok Shop.  
**API Partner** existe para sellers/partners automatizarem catálogo e links, mas exige app aprovado no Partner Center; para MVP basta CMS + links gerados no app.

Disponibilidade do **External Traffic Program (ETP)** / Affiliate Links **varia por mercado e conta**. Guias oficiais confirmam compartilhar em websites/redes; fontes BR descrevem ETP em 2026, mas **só o painel do `@anderzilla` prova** se “Copiar link” afiliado já aparece.

## Dois papéis (não misturar)

| Papel | O que você posta no site | Monetização |
|-------|--------------------------|-------------|
| **Seller** (loja própria) | Link da loja / PDP / showcase da **sua** Shop | Venda na TikTok Shop (não comissão afiliada de si mesmo no sentido clássico) |
| **Creator afiliado** (ETP) | Affiliate Links rastreados (produto, campanha, showcase, shop de terceiros) | Comissão após pedido **fulfilled**; age verify + banco no creator |

Anderson pediu “links para a minha loja” **e** “links afiliados”: no hub, tratar como placements `market=br` (ou intl se houver) com tipo `tiktok_shop_product` / `tiktok_shop_showcase` / `tiktok_affiliate`.

## O que a documentação oficial descreve (ETP / Affiliate Links)

Fonte: [Affiliate Links Guide for Creators (SG Academy, 2026-06-23)](https://seller-sg.tiktok.com/university/essay?knowledge_id=1653513001436945&lang=en)

- ETP: creators geram links e compartilham em **social, websites, apps**.
- Tipos: Product, Campaign, Showcase (só Affiliate Creator), Shop Page.
- Age verification obrigatória; sem isso o link pode ser “regular” **sem comissão**.
- Dados bancários no creator para receber.
- Atribuição: janela tipicamente **7 dias** (direct/indirect); validade do link até **~100 dias** — depois regenerar.
- Comissão após **fulfillment**, não só checkout.

US Academy (sharable links): Share → Copy Link; colar em bio, newsletter, etc.

Política BR de conteúdo ([seller-br Content Policies](https://seller-br.tiktok.com/university/essay?knowledge_id=1413208980588305)): **dentro** do conteúdo TikTok Shop, proíbe CTAs que tirem o usuário da Shop (site externo, QR, etc.). Isso **não impede** o inverso (site próprio → TikTok Shop); só reforça que o checkout deve permanecer na TikTok.

## Integrações possíveis (do mais simples ao mais pesado)

### A) MVP recomendado — CMS manual (1–2 dias)

1. No app TikTok: Showcase / produto → Share → **Copy link** (afiliado se ETP ativo).
2. No AnderZilla CMS: placements com título PT/EN, imagem (autorizada), URL HTTPS, `market`, `rel=sponsored noopener noreferrer`, disclosure.
3. Rota hub ex.: `/[lang]/loja-tiktok` ou bloco na Área Brasil / Loot.
4. Sem API; Anderson atualiza links quando expirarem (~100 dias afiliado).

### B) Semi-auto — planilha/JSON import

Mesmo modelo; lote via newsroom/import existente; ainda sem OAuth TikTok.

### C) Partner / Seller API (médio-longo)

- [Partner Center](https://partner.tiktokshop.com/docv2/page/tts-api-concepts-overview): apps, tokens, `shop_cipher`.
- Seller Product APIs: listar catálogo.
- Affiliate Partner: gerar links de campanha (`/affiliate_partner/.../links/generate`) — perfil **partner/agência**, não “site pessoal” típico.
- Custo: aprovação de app, escopos, manutenção OAuth, não publicar secrets no Git.

**Não usar scrapers** de terceiros como integração oficial (ToS / fragilidade).

## O que **não** fazer

- Checkout / carrinho no anderzilla.com fingindo ser TikTok Shop.
- Embed não oficial que quebre deep link / atribuição.
- Marcar placement `ativo` sem URL real da conta.
- Prometer comissão se ETP/age verify não estiver liberado na conta BR.
- Colocar dados bancários TikTok no repositório.

## Checklist na conta `@anderzilla`

- [ ] TikTok Shop ativo (seller e/ou creator afiliado)
- [ ] Age verification OK
- [ ] Banco/payout creator preenchido (se quiser comissão ETP)
- [ ] Consegue Share → Copy Link com preview de comissão?
- [ ] Link da Showcase / shop page copia e abre no browser
- [ ] Mercado BR confirmado no Seller/Creator Center

## Encaixe AnderZilla

- Registro: `mon-tiktok-shop-links` · market preferencial `br`
- Disclosure Trust: “Links levam à TikTok Shop; podemos receber comissão afiliada quando aplicável.”
- Não misturar com Karaca Points (não premiar clique em afiliado).

## Fontes

- https://seller-sg.tiktok.com/university/essay?knowledge_id=1653513001436945&lang=en  
- https://seller-us.tiktok.com/university/essay?knowledge_id=4308436637255466&lang=en  
- https://partner.tiktokshop.com/docv2/page/tts-api-concepts-overview  
- https://seller-br.tiktok.com/university/essay?knowledge_id=1413208980588305  