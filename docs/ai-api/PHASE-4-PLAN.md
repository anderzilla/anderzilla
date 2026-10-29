# Fase 4 — publicação com Azure (plano; nada foi criado)

## Resultado da etapa 4a (2026-10-29, local, sem Azure)

O corpus de produção foi importado para um SQLite local e o site inteiro foi construído **a partir do banco**. Comparado com o artefato que está no ar (`.deploy/production-20261029`):

- **Dados:** 71 notícias, 242 mídias e o produto ForgeKit fazem a ida e volta pelo CMS sem nenhuma diferença (`import_corpus.py`).
- **Site:** 669 arquivos idênticos, incluindo as 242 imagens WebP e as 231 imagens sociais, byte a byte.
- **Diferenças, todas explicadas:**
  - 22 páginas (11 notas do Radar, PT e EN) trocam o `og:image` de `.webp` para `-social.jpg`, e há 11 arquivos `-social.jpg` novos. Essas 11 notas nunca tiveram imagem social; é uma melhoria, não uma regressão.
  - `sitemap.xml`: mesmas 174 URLs, só muda o `lastmod` dos 32 itens que usam a hora do build.
  - `cms-release.json`: o marcador de release muda porque o snapshot é outro.
- **Três lacunas do modelo, corrigidas no código:**
  1. `observed` é por notícia (60 em 17/09, 10 em 28/10, 1 em 29/10) e o transform usava a data do release; agora é o campo `observedAt`, carimbado na primeira aprovação e nunca recalculado.
  2. 4 notas têm `updatedAt` editorial, que o transform ignorava e o site usa para ordenar o Radar; agora é `editorialUpdatedAt`, publicado só quando existe.
  3. O ForgeKit aparecia por um *fallback* do site (`commerce/data.ts`) que deixa de valer quando o banco publica `products: []`; sem o registro no banco, a página perdia o card. O importador cria o registro com o texto idêntico ao do site (um teste mantém os dois em sincronia).
- **Ressalvas:** a importação lê o corpus do worktree de documentação e as imagens do bundle `.deploy/`, ambos locais; o banco Azure não foi tocado. O artefato registra `deployed: false` no JSON, mas o log de 29/10 e a data de modificação da produção mostram que foi publicado.
- **Portão da 4a cumprido:** o banco reproduz o site de hoje. A etapa 4b (criar recursos Azure) continua exigindo a sua aprovação.

Data: 2026-10-29. Somente leitura: inventário do Azure, do repositório e da produção. Nenhum recurso foi criado, nenhum deploy foi feito.

## O que a investigação mudou no plano

1. **A produção não nasce do banco.** O artefato de produção sai de `infra/azure/rebuild-production.py`, que usa o corpus `public-after.json` do worktree `G:\AnderZilla-docs` (71 notícias, 242 mídias) e 462 arquivos de imagem do bundle `.deploy/` (fora do Git). O banco `anderzilla-cms-homolog` provavelmente está defasado em relação a esse corpus (as 11 notas de 28–29/10 entraram pelo corpus; não verifiquei o banco). Antes de qualquer cutover, o banco precisa ser populado **a partir do corpus** e provar que gera o mesmo site.
2. **Publicar o `out/` do repositório quebra 231 imagens.** Esses arquivos só existem no bundle. Corrigi `docs/DEPLOY.md`, `CLAUDE.md`, `/ajuste` e `/publicar` na branch `ajuste/fluxo-publicacao` (commit `1b7b148`).
3. **Cota de imagens no banco:** 22,4 de 32 MiB já usados (base64). Cabem cerca de 25 imagens novas. Imagens passam para Blob Storage antes de a API entrar em uso.
4. **Branch padrão do repositório `AnderZilla-Web` é `codex/anderzilla-docs`.** Workflows disparados por API/`repository_dispatch` só rodam com o arquivo na branch padrão. É preciso trocar a branch padrão para a foundation (ou `main`).
5. **`api.anderzilla.com` já está reservado** no plano de identidade (`infra/azure/IDENTITY-PLAN.md`). A API para IAs usa outro host.

## Estado do Azure hoje (conta `anderzilla@ymail.com`, grupo `anderzilla-web`)

| Recurso | Situação |
|---|---|
| SWA `anderzilla-web-production` / `-homolog` | Free; produção com `anderzilla.com` e `www` Ready; homolog privado |
| SWA `anderzilla-admin-homolog` | Free; painel antigo |
| SWA `anderzilla-identity-homolog` / `-production` | Free |
| SQL server `anderzilla-sql-44b76346-cus` | 3 bancos, todos na oferta gratuita (limite de 10), autopause 60 min, hoje pausados; firewall: serviços Azure + 1 IP local |
| Function App `anderzilla-identity-api` | Python 3.11, plano de consumo Linux compartilhável |
| Storage `anderzillaidentityst` | Standard_LRS, acesso público de blob desligado |
| GitHub Actions | habilitado, repositório privado, sem environments |

## Arquitetura alvo

```
IA (Claude, ChatGPT, Gemini, Grok)
   │  chave por agente (hash)           OpenAPI / MCP
   ▼
Function App  ia.anderzilla.com  ──►  SQL  anderzilla-cms-production  ◄──  Review SWA  revisao.anderzilla.com
   │ rascunhos, mídia, pacotes                     ▲                           │ login Microsoft (anderzilla_admin)
   ▼                                               │                           │ aprovar · comentar · promover · rollback
Blob (imagens)                                     │                           ▼
                                                   └───────────  GitHub Actions  (build do site a partir do snapshot)
                                                                  ├─ prévia por pacote  → homolog SWA, ambiente pv-<id> (privado)
                                                                  ├─ release aprovado   → homolog SWA → verificação
                                                                  └─ promoção (humana)  → produção SWA, mesmo artefato
```

- **API das IAs:** Function App próprio (o SWA gerenciado limita o corpo a 300 KB; uma imagem em base64 passa de 2,8 MB).
- **Rotas humanas:** API gerenciada do SWA de revisão; o principal vem do login Microsoft do SWA (já é o padrão do `services/cms`).
- **Ambientes:** banco `anderzilla-cms-homolog` vira sandbox de testes dos agentes; `anderzilla-cms-production` é a fonte de verdade. Homolog é uma etapa do release, não um segundo conteúdo.
- **Build:** o Actions baixa o snapshot por uma rota de máquina autenticada (padrão `/api/worker/` com OIDC que já existe), constrói, publica o artefato como artifact do run e faz o deploy. Rollback = redeploy do artifact do run anterior.
- **Segunda barreira:** o workflow de produção só roda se a API confirmar que o release foi **promovido por um humano**; ter acesso ao Actions não basta.

## Etapas e portões

| Etapa | O que faz | Cria recurso? | Portão para a próxima |
|---|---|---|---|
| **4a** | Importar `public-after.json` + imagens do bundle para um SQLite local, gerar o snapshot, construir e comparar com `anderzilla.com` | Não (local) | 182/184 páginas idênticas e 462 hashes de mídia iguais |
| **4b** | Provisionar: banco `anderzilla-cms-production` (gratuito), Function App da API, SWA de revisão, Blob de mídia, escopos de segurança. Scripts com `-WhatIf` primeiro | **Sim (pede sua aprovação)** | Recursos conferidos pela CLI |
| **4c** | Implantar API e revisão em **homolog/sandbox**; DNS `ia.` e `revisao.`; testar com um agente de verdade | Sim (DNS Wix) | Fluxo completo agente → prévia → aprovação em homolog |
| **4d** | Workflow de build/deploy no Actions; trocar a branch padrão; secrets por ambiente (você cola os tokens no GitHub, nunca no chat) | Config GitHub | Release de teste construído e publicado em homolog |
| **4e** | Importar o corpus no banco de produção; primeiro release dirigido pelo banco em homolog, comparação com a produção, só então promoção | Dados | Paridade comprovada; fluxo manual atual fica como contingência por pelo menos 3 releases |

## Custo estimado (teto do projeto: R$ 150/mês)

| Item | Estimativa |
|---|---|
| SQL de produção (oferta gratuita, 4 de 10 bancos) | R$ 0 (se esgotar o limite mensal, autopause) |
| Function App (plano de consumo, franquia mensal gratuita) | R$ 0 a poucos reais |
| SWA de revisão (Free) | R$ 0 |
| Blob Storage (≈ 50 MiB, LRS) | centavos |
| GitHub Actions (repositório privado, 2.000 min/mês; cada build 3–5 min) | R$ 0 |
| DNS (registros no Wix) | R$ 0 |
| **Total** | **≈ R$ 0 a R$ 10/mês** |

## Riscos

- **Cold start:** o banco pausa após 60 min; a primeira chamada pode levar cerca de 1 minuto. Os agentes precisam repetir a chamada (a idempotência já cobre isso).
- **Limite gratuito do SQL:** ao esgotar, o banco pausa até o mês seguinte (sem cobrança). A API fica indisponível nesse período; o site estático não é afetado.
- **Prévia em iframe:** cookies de terceiros podem bloquear o login do homolog dentro do iframe (já houve `ERR_BLOCKED_BY_CLIENT`). Plano B: botão "Abrir em outra aba".
- **Proteção de ambiente do GitHub** em repositório privado pode exigir plano pago; por isso a barreira de produção fica na API.
- **Vazamento de chave de agente:** escopo por coleção, validade, revogação e criação de rascunhos apenas; sem permissão de aprovar.
- **Migração de dados:** é o maior risco e por isso 4a vem primeiro e é local.

## O que só você pode fazer

- Aprovar a criação de recursos (4b) e do DNS (4c).
- Criar os registros DNS no Wix, se eu não tiver acesso, e colar os tokens do SWA nos environments do GitHub (4d).
- Trocar a branch padrão do repositório `AnderZilla-Web` (4d).
- Decidir os nomes `ia.anderzilla.com` e `revisao.anderzilla.com`.
