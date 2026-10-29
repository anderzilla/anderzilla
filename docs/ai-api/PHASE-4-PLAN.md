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

## Resultado do dry-run da etapa 4b (2026-10-29, nada criado)

`infra/azure/content-provision.ps1 -Environment homolog|production` inspeciona o Azure, imprime o que seria criado, o custo e os comandos exatos. Sem `-Apply` é somente leitura; com `-Apply` ainda respeita `-WhatIf` e `-Confirm`. Rodei os dois ambientes e `-Apply -WhatIf`; a contagem de recursos do grupo ficou em 16 antes e depois.

| Recurso | Homolog | Produção | Custo |
|---|---|---|---|
| Banco do CMS | `anderzilla-cms-homolog` já existe (reaproveitado como sandbox) | `anderzilla-cms-production` (novo, oferta gratuita, 4 de 10) | R$ 0 |
| API das IAs | `anderzilla-content-api-homolog` (Function App, plano Y1 existente) | `anderzilla-content-api-production` | R$ 0 dentro da franquia mensal |
| Armazenamento de mídia | conta `anderzillacontentst` + contêiner privado `media-homolog` | contêiner `media-production` na mesma conta | centavos |
| Página de revisão | opcional (`-NoReviewSite`) | `anderzilla-review-production` | R$ 0 |

- **Limite de SWAs gratuitas:** a assinatura já tem **8 de 10** (as 5 da AnderZilla mais `codematrix-agency`, `codematrix-corporate` e `ia-engineer-course`). Duas páginas de revisão ocupariam as últimas vagas. Proposta: **uma única** página de revisão (`anderzilla-review-production`) e o sandbox testado com o servidor local; ou aposentar `anderzilla-admin-homolog`, que a revisão substitui.
- Nomes verificados como livres: conta de storage `anderzillacontentst` e hosts `anderzilla-content-api-*.azurewebsites.net`.
- O caminho `-Apply` ainda não foi exercitado de verdade (só `-WhatIf`), por desenho; a primeira execução real deve ser a de homolog.
- Fora do escopo desta etapa e feito depois, um passo por vez: esquema do banco e usuário SQL de runtime, configurações do app, permissão da identidade da API no contêiner, deploy do código, DNS (`ia.` e `revisao.`) e segredos do GitHub.

## Homolog criado (2026-10-29, aprovado pelo proprietário)

Criados e conferidos pela CLI e pelo ARM no grupo `anderzilla-web` (16 → 20 recursos; SWAs continuam em 8). A Function App foi **recriada em Flex Consumption** depois de a primeira versão (plano Linux Consumption) ficar meio provisionada; veja as lições abaixo.

| Recurso | Estado verificado |
|---|---|
| Storage `anderzillacontentst` | StorageV2, Standard_LRS, TLS 1.2, só HTTPS, acesso público de blob desligado |
| Contêiner `media-homolog` | privado (sem acesso público) |
| Function App `anderzilla-content-api-homolog` | **Flex Consumption (FC1)**, Python 3.12, 2048 MB por instância, **máximo de 10 instâncias**, plano próprio `ASP-anderzillaweb-1af9`, HTTPS obrigatório, identidade gerenciada atribuída ao sistema, armazenamento de deploy por identidade (sem chaves); `https://anderzilla-content-api-homolog.azurewebsites.net` (sem código implantado) |
| Application Insights `anderzilla-content-api-homolog` | criado automaticamente pela CLI; gratuito até 5 GB/mês |
| Permissão da identidade da app | a CLI concedeu *Storage Blob Data Contributor* **na conta** `anderzillacontentst` (necessário para o armazenamento de deploy por identidade). É mais amplo que "só o contêiner de mídia", mas a conta só contém os dados desta plataforma. O script `content-grant-storage.ps1` ficou redundante e foi removido |
| Configurações da app | `CMS_SQL_SERVER`, `CMS_SQL_DATABASE`, `CMS_SQL_USER`, `CMS_SQL_PASSWORD`, `CMS_ENVIRONMENT` aplicadas e verificadas por `content-configure.ps1` (a senha nunca foi exibida); `AGENT_MEDIA_HOSTS` e `CMS_REVIEW_BASE` não definidas de propósito |

Banco `anderzilla-cms-homolog` reaproveitado (existia). Nenhuma SWA criada.

**Tropeços e lições (já refletidos em `content-provision.ps1`):**
- **A primeira Function App (Linux Consumption no plano `EastUS2LinuxDynamicPlan`) ficou meio provisionada:** leitura e PATCH do site funcionavam, mas toda escrita de configuração e a exclusão falhavam com "Cannot find ServerFarm" / "Unable to resolve the App Service plan for delete validation". Conclusão minha a partir desses sintomas, não confirmada pela Azure. Com a aprovação do proprietário, apaguei a app e seu Application Insights (ambos meus, vazios) e recriei em Flex Consumption, que funcionou de primeira.
- **Exclusão:** `az rest --method delete` só funcionou com `--url-parameters deleteEmptyServerFarm=false deleteMetrics=false`. Um `&` dentro da URL é mutilado pelo `az.cmd` (o `cmd` o trata como separador); use sempre `--url-parameters`.
- **Python 3.12 e não 3.11:** no Flex, o 3.11 sai de suporte em 10/2027 e o 3.12 em 10/2028; o código já é testado em 3.12.
- **Linux Consumption** perde o suporte em 30/09/2028 (aviso do Azure). O `anderzilla-identity-api` ainda está no plano antigo e tem o mesmo prazo; não foi tocado.
- Reexecutar `content-provision.ps1 -Apply` em homolog é idempotente (20 recursos, nada novo) e o script agora confere pelo ARM que a app é Flex, Python 3.12, com no máximo 10 instâncias e fora do plano antigo.

**Próximos passos de homolog (cada um separado e revisado):** deploy do código da API (o esquema do banco e as configurações já foram aplicados), primeira chave de agente, teste de um fluxo real e DNS `ia.`.

## API das IAs: adaptador e configuração preparados (2026-10-29, **nada aplicado nem implantado**)

- **Adaptador** `services/content-api/` (`content_api.py` + `function_app.py`, `host.json` sem prefixo `/api`, `requirements.txt` fixado). A app é pública, então só aceita **chave de agente**: qualquer `x-ms-client-principal` ou cookie enviado pelo cliente é ignorado e as rotas humanas (aprovar, comentar, pedir correções, prévia, promover) respondem 401 aqui; elas ficam atrás do login Microsoft da página de revisão. `GET /v1/health` é público e não toca o banco. Corpos: 300 KB, ou 3 MB em `/v1/media`; só `application/json`; sem CORS; `Cache-Control: no-store`; falhas de infraestrutura viram 503 sem detalhes e com `Retry-After: 30`.
- **Testes** (10, `services/content-api/`): autenticação e desafio `Bearer`, identidade forjada, validação de requisição, limite por rota, fluxo agente (rascunho e pacote, mas não aprovação), 503 sanitizado, cabeçalhos, e um teste de empacotamento que importa o pacote **plano** (sem o layout do repositório) e acusa arquivo faltando. Suítes: CMS 137, publisher 36, content-api 10.
- `infra/azure/content-configure.ps1`: mescla `CMS_SQL_SERVER/DATABASE/USER/PASSWORD` e `CMS_ENVIRONMENT` nas configurações da app, lendo o arquivo da credencial de runtime. Dry-run por padrão, imprime só nomes (a senha aparece como `(hidden)`), preserva as 5 configurações existentes, usa corpo temporário com ACL restrita e confere o resultado depois. Não define `AGENT_MEDIA_HOSTS` (vazio = a API recusa buscar imagens por URL) nem `CMS_REVIEW_BASE` (a revisão ainda não existe).
- **Atualização:** as configurações foram **aplicadas** em homolog depois da recriação da app em Flex (ver acima); o script `content-grant-storage.ps1` foi removido por ficar redundante.
- **Falta (cada passo com aprovação):** empacotar e implantar o código (dependências Linux, como em `deploy-admin.ps1`; verificar pelo ARM e pelo `/v1/health`); criar a primeira chave de agente; testar um fluxo real. O endereço `/v1/health` ainda não respondeu (`curl` devolveu erro de conexão, esperado sem código implantado); revisar depois do deploy.

## Esquema do banco de homolog: APLICADO (2026-10-29, pelo proprietário no próprio terminal)

O proprietário redefiniu a senha do administrador SQL no portal (ninguém tinha a anterior; ela ficara no ambiente antigo do Codex) e rodou `content-migrate.ps1 -Environment homolog -Apply`. Saída: "Content schema and runtime grants applied; permission checks passed." O login correto é `anderzilla_bootstrap` (as duas primeiras tentativas falharam por usar `anderzilla@ymail.com` e `anderzilla`; o SQL não alterou nada).

Conferido sem abrir segredos: o arquivo `C:\Users\ander\.codex\anderzilla-azure\content-api-homolog.json` existe (314 bytes), está fora do repositório, com herança de permissões bloqueada e acesso só do usuário `ander`; contém os campos `environment, server, database, user, password, createdAt`. Não li os valores.

**Não verificado:** o conteúdo do banco (não há credencial de leitura nesta sessão); a confirmação vem das verificações de permissão feitas dentro da transação antes do commit e do próprio `Applied`.

## Esquema do banco de homolog (como foi preparado)

`infra/azure/content-migrate.ps1 -Environment homolog` aplica o esquema aditivo em `anderzilla-cms-homolog` e cria o usuário SQL de runtime `anderzilla_content_runtime`. Sem `-Apply` é um dry-run que valida os arquivos SQL e o alvo no Azure e **nunca abre conexão**.

- **Verificações estáticas:** só `IF OBJECT_ID/NOT EXISTS … CREATE` (sem DROP, TRUNCATE, DELETE, ALTER nem EXEC) e só `GRANT/DENY` para o usuário de runtime, sem `db_owner`, `CONTROL`, `ALTER` ou `EXECUTE`. As 11 tabelas têm `SELECT` concedido.
- **Teste de paridade** (`services/cms/test_schema_parity.py`, 4 testes): o esquema SQLite dos testes e o do Azure têm as mesmas tabelas, colunas e índices; as permissões cobrem toda tabela, negam `DELETE` em todas, negam `UPDATE` em auditoria, revisões, requisições e comandos, e a chave de agente só permite atualizar a coluna `document` (revogar), nunca o hash.
- **Dentro da transação, antes do commit**, o `-Apply` impersona o usuário de runtime e confere (`HAS_PERMS_BY_NAME`): pode inserir/atualizar registros, não pode apagar nada, não atualiza auditoria nem revisões, não é `db_owner`. Qualquer falha desfaz tudo.
- **Credenciais:** o administrador SQL (`anderzilla_bootstrap`) é pedido de forma interativa (`Get-Credential`), nunca por argumento, arquivo do repositório ou chat. A senha do usuário de runtime é gerada localmente (48 caracteres aleatórios) e gravada só em `C:/Users/ander/.codex/anderzilla-azure/content-api-homolog.json`, com permissão restrita ao seu usuário do Windows, e nunca é exibida. Um usuário que já exista mantém a senha, salvo `-RotateRuntimePassword`.
- **Firewall:** o IP público desta máquina (191.177.44.56) já tem regra no servidor SQL.
- **Ressalva:** o T-SQL do `-Apply` ainda não foi executado contra um SQL Server (só foram testados a análise estática, a paridade e o `-WhatIf`); a transação com verificação e rollback é a rede de segurança. O esquema atual dos bancos não foi lido.

Comando para rodar **no seu terminal** (ele pede a senha do administrador na hora):

```powershell
./infra/azure/content-migrate.ps1 -Environment homolog -Apply
```

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
