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

## Página de revisão em homolog: FUNCIONANDO (2026-10-29)

**Teste real, com a sessão logada do proprietário (somente leitura):** `/.auth/me` com `anderzilla_admin`; `/` carrega a interface; `GET /api/v1/submissions` devolve 200 e a lista mostra os 2 pacotes pendentes de teste ("Smoke test d93578c9" e "Teste end-to-end automatizado"); o detalhe de um pacote carrega (`/items` 200) com a imagem, alt PT/EN, crédito, licença e fonte, o campo de comentário e o aviso de licença declarada; a prévia responde 501, como previsto. Nada foi aprovado nem comentado nesse teste.

**O que deu errado e a causa:**
1. **403 por cerca de 40 minutos depois do convite.** O papel aparecia no Azure (`az staticwebapp users list`) logo após o convite, mas só chegou à sessão (`/.auth/me`) muito depois, mesmo com logout e novo login; é um atraso de propagação do SWA, não um erro de e-mail nem de link (o e-mail do login batia com o do convite). **Lição:** depois de aceitar um convite, espere e confira o `/.auth/me` antes de mexer na configuração.
2. **Plano B inviável no plano Free.** Tentei atribuir o papel por função (`auth.rolesSource` no `staticwebapp.config.json`); o serviço recusou: *"The 'auth' configuration … is only supported on the Standard SKU"*. O deploy falhou sem alterar o site, e o commit do plano B foi revertido (`9da6df5`). A setting `REVIEW_ADMIN_USER_IDS` ficou aplicada no site, sem uso nenhum; é só um identificador e pode ser removida depois. Padrão Standard custa cerca de US$ 9/mês e só valeria se o convite voltar a falhar.
3. **503 na primeira chamada.** O banco serverless pausa após 60 minutos e a primeira requisição depois da pausa estoura a conexão enquanto ele acorda (a segunda vem 200). Correções no código, **ainda não implantadas**: tempo de login do banco de 15 para 40 s (o SWA corta uma requisição em ~45 s); a interface repete as leituras até 3 vezes com intervalo de 5 s e avisa que a primeira abertura pode levar até 1 minuto (escritas nunca são repetidas sozinhas); o menu de campos do comentário deixa de listar campos técnicos (hash, tipo MIME, largura etc.).

**Reimplantado com as correções (2026-10-29, pacote da API `6ac1ba5f02cf`):** o script confirmou de fora que `/`, `/api/v1/health`, `/api/v1/submissions` e um arquivo estático seguem redirecionando para o login Microsoft. No Chrome do proprietário a lista abre com os 2 pacotes e o detalhe da notícia mostra só os campos úteis no menu de comentário (sem hash, tipo MIME, largura etc.). A repetição automática da primeira abertura só se exercita com o banco pausado e ainda não foi vista em ação.

**Teste do ciclo completo contra o SQL Azure real: 29/29 verificações passaram** (depois de o proprietário liberar a permissão; a primeira execução falhou por um erro do meu script, que passava o caminho com o prefixo `/v1/`). O agente prepara o pacote pela API implantada; o código real da API de revisão, com um humano simulado (id de teste, nunca o do proprietário), lista, vê itens e miniatura, comenta em campo e em registro inteiro, recusa campo inexistente e registro de outro pacote, pede correções, recusa aprovar enquanto há correções; o agente lê os comentários, corrige e reenvia (rodada 2); o humano vê o título corrigido e o comentário resolvido, aprova (release enfileirado, 3 registros aprovados), lê o status do release (o agente também lê o do seu), e a aprovação dupla, o comentário depois de aprovado, a prévia e a promoção são recusados (409/501); sem principal 401, sem papel 403, POST de outra origem 403, chave de agente 401; a auditoria registra as ações do agente e do humano separadamente.

**Achado: aprovar levava 138 s (o SWA corta em ~45 s).** Causa: o snapshot de cada release **embutia as 232 imagens em base64 (21 MiB)** e gravar isso no SQL Azure levava mais de um minuto. Correções (commit seguinte a este registro), todas testadas e validadas no banco real:
1. O snapshot do release passa a **referenciar** as imagens (`assetSha256` e `url`; `assets: by-reference`): 21,1 MiB → 619 KiB. A leitura das mídias usa `JSON_MODIFY` no próprio banco, de 3,3 s para 1,3 s.
2. O publisher carrega as imagens por id **e confere cada SHA-256** antes de construir (`hydrate_assets`; recusa bytes diferentes do aprovado). Todas as 232 em **2,5 s** numa consulta só (a primeira versão, uma a uma, levava 68,6 s).
3. Conexão do SQL **reutilizada por thread**, com checagem antes do uso, descarte se quebrar e **recusa de transação aninhada** (que antes causaria deadlock no lock da aplicação); tempo de login 15 → 40 s.
4. Prévias e builds de paridade continuam usando o snapshot completo (com imagens).

**Tempos medidos da máquina do proprietário (latência alta até o Azure, ~0,3 s por consulta):** aprovar 138 s → 33,8 s → 29,0 s (e 23,6 s num pacote de 2 registros). Dentro do Azure (Function em eastus2, banco em centralus) a latência é bem menor, então o tempo real deve ser inferior; **ainda não medido no ambiente implantado**. A cota de 32 MiB deixa de ser checada na criação do release (é aplicada no upload); o snapshot completo continua rejeitando acima do teto.

**Dados de teste que ficam no banco de homolog** (a credencial de runtime não apaga): 7 pacotes de teste (2 pendentes antigos e 5 criados por estes testes, com registros aprovados e releases na fila), todos marcados `isDemo`. Suítes: CMS 149, publisher 36, content-api 25, review-api 10. **Falta reimplantar o site de revisão** para a correção valer na página real.

### Estado anterior (criação e implantação)

## Página de revisão em homolog: criada, configurada e implantada (2026-10-29)

Com a aprovação do proprietário: SWA `anderzilla-review-homolog` criado (**Free**, East US 2, confirmado pelo ARM; 9 de 10 SWAs; 21 recursos no grupo) em `https://victorious-river-0830f700f.6.azurestaticapps.net`. Configurações aplicadas e verificadas (`CMS_SQL_SERVER/DATABASE/USER/PASSWORD`, `CMS_ENVIRONMENT`, `REVIEW_ALLOWED_ORIGIN`; senha nunca exibida). Implantado pelo `deploy-review.ps1`; a API gerenciada registrou a função `review_api` (HttpTrigger).

**Verificação anônima, de fora:** `/`, `/api/v1/health`, `/api/v1/submissions` e `/brand/lettering.webp` respondem **302 para `/.auth/login/aad`**; `http://` dá 301 para HTTPS; `/.auth/me` anônimo devolve `clientPrincipal: null`; as respostas trazem `x-robots-tag: noindex, nofollow`, `Cache-Control: no-store`, `nosniff` e `no-referrer`. Ou seja, **nada do site nem da API é alcançável sem entrar**.

**Tropeço (já corrigido no script):** o SWA CLI escreve o progresso no stderr; com `ErrorActionPreference='Stop'` o PowerShell tratou isso como erro e abortou o script **depois** de o deploy ter terminado, então a verificação final não rodou na primeira vez. Confirmei o estado por fora (ambiente `Ready`, rotas redirecionando, função registrada), corrigi o script para julgar só pelo código de saída e rodei o fluxo inteiro de novo: deploy e verificação passaram. Os 2 processos `node` restantes na máquina não são do deploy.

**Falta:** o **convite** (`review-invite.ps1 -Environment homolog -Apply`), que deve ser rodado pelo proprietário no próprio terminal porque o link de uso único aparece na tela; entrar com `anderzilla@ymail.com` e conferir os 2 pacotes de teste pendentes. Riscos: o login `aad` pré-configurado pode não aceitar a conta pessoal `ymail.com` e um bloqueador de anúncios pode barrar `identity.*.azurestaticapps.net`; nenhum dos dois foi testado ainda.

### Como estava preparada

## Página de revisão em homolog: preparação (2026-10-29)

**Arquitetura:** Static Web App Free `anderzilla-review-homolog` com login Microsoft (provedor `aad`) e a UI estática de `apps/review`; a API de revisão é a **API gerenciada** do próprio SWA (`services/review-api/`, Python 3.11, único suportado), então ela só é alcançável por trás do login do SWA. A API da fase anterior (`ia.`) continua separada e só aceita chaves de agente.

- **`services/review-api/review_api.py`:** a identidade vem **somente** do `x-ms-client-principal` do SWA (decodificado e validado: usuário autenticado, papéis como lista de textos); sem o papel `anderzilla_admin` as rotas humanas dão 403. **Chaves de agente nunca são aceitas aqui** (rotas de agente respondem 401, mesmo com chave válida). Como o login é por cookie, todo POST exige `application/json` e `Origin` igual ao do site (`REVIEW_ALLOWED_ORIGIN` ou o host encaminhado); não há CORS. Corpo máximo de 300 KB, 503 sem detalhes, `no-store`. Prévia e promoção respondem 501 (a interface mostra "prévia ainda não disponível neste ambiente" em vez de erro).
- **Testes** (10 em `services/review-api/`): identidade forjada ou mal formada (401), logado sem papel (403), chave de agente recusada, ciclo humano completo (listar, itens, comentar, pedir correções, reenvio pelo agente, aprovar com release enfileirado), CSRF/Origin, limites, cabeçalhos, 503 sanitizado e pacote plano importável. Suítes: CMS 137, publisher 36, content-api 25, review-api 10.
- **Empacotamento:** `package_content_api.py --profile review` (wheels Linux cp311, só as fontes da lista, mesmas varreduras). Pacote da API 13 MiB, 1154 arquivos, sem binários Windows; UI com 34 arquivos e base `/api` embutida.
- **`infra/azure/deploy-review.ps1`** (dry-run construído e conferido): confere que **só `/.auth/*` é anônimo**, que a rota `/*` exige exatamente `anderzilla_admin`, que o runtime é `python:3.11` e que nenhum arquivo proibido vai junto; com `-Apply` implanta pelo SWA CLI 2.0.10 (token lido do `az`, nunca impresso) e depois verifica anonimamente que `/`, `/api/v1/health`, `/api/v1/submissions` e um arquivo estático **redirecionam para o login Microsoft**; se qualquer um não redirecionar, o script falha.
- **`review-configure.ps1`** (dry-run): `CMS_SQL_*`, `CMS_ENVIRONMENT` e `REVIEW_ALLOWED_ORIGIN`, a senha só como `(hidden)`.
- **`review-invite.ps1`** (dry-run): convite com o papel `anderzilla_admin` para `anderzilla@ymail.com`; o link de uso único aparece **só no terminal de quem roda** (rodar você mesmo).
- **UI:** com `NEXT_PUBLIC_REVIEW_API_BASE=/api` ela chama a API do mesmo site; o painel de prévia some quando o ambiente responde 501.

**Impacto nos limites e custo:** a conta tem 8 de 10 SWAs gratuitas; criar esta leva a 9. Sem custo (SWA Free; SQL e Function já existentes). A mesma credencial de runtime (`anderzilla_content_runtime`) passa a ser usada pela API de revisão e pela API das IAs; usuários separados seriam melhores e exigem um parâmetro de arquivo de segredo no `content-migrate.ps1` (não feito).

**Riscos conhecidos:** (1) o login `aad` pré-configurado do SWA já falhou antes neste projeto (`ERR_BLOCKED_BY_CLIENT` em `identity.*.azurestaticapps.net`, provavelmente bloqueador de anúncios no navegador); (2) o provedor pré-configurado pode não aceitar a conta pessoal `ymail.com` neste tenant (não verificado); (3) o banco de homolog pausa após 60 min, a primeira abertura pode demorar cerca de 1 minuto; (4) sem prévia fiel até o pipeline de build existir.

**Passos que faltam, cada um com aprovação:** criar o SWA (`content-provision.ps1 -Environment homolog`, sem `-NoReviewSite`), aplicar as configurações, implantar, convidar e entrar.

## API das IAs em homolog: IMPLANTADA e verificada (2026-10-29)

`infra/azure/deploy-content-api.ps1 -Environment homolog -Apply` empacotou e implantou o código na Function App Flex (pacote `c2bebbc20c2b`, 13,1 MiB; guardado em `.deploy/content-api-homolog-20261029T141425/` para rollback, fora do Git). O empacotador (`infra/azure/package_content_api.py`) copia só 8 arquivos de uma lista explícita, instala dependências como **wheels Linux** (cp312, manylinux; sem `__pycache__` nem `.exe`), varre as fontes atrás de segredos, recusa arquivos proibidos (`.env`, `.pem`, `.sqlite`, `.exe`, credenciais; só o `cacert.pem` público do certifi é permitido) e gera um zip reprodutível (mesmas entradas, mesmo hash). 6 testes novos; `services/content-api` tem 16.

Verificado **de fora** em `https://anderzilla-content-api-homolog.azurewebsites.net` (e pelo ARM: a função `content_api` está registrada):

| Chamada | Resultado |
|---|---|
| `GET /v1/health` | 200 `{"status":"ok"}` |
| `GET /v1/schema` sem chave | 401 |
| `GET /v1/schema` com chave inválida | 401 (a recusa só acontece depois de consultar a tabela `agent_keys`; prova conexão, credencial de runtime e esquema) |
| `POST /v1/submissions/x/approve` com `x-ms-client-principal` forjado | 401 |
| `POST /v1/articles` com `text/plain` | 415 |
| `GET /api/v1/health` (prefixo antigo) | 404 (a rota é `/v1/...` mesmo) |
| `http://…` | 301 para HTTPS |

Todas as respostas JSON trazem `Cache-Control: no-store` e nenhuma tem cabeçalho CORS. `DELETE /v1/articles` devolve 404 do próprio host (a rota só aceita GET e POST), não o 405 do adaptador; sem impacto de segurança.

**Chaves de agente (ferramenta local, preparada; nenhuma chave criada ainda):** `infra/azure/content-key.ps1 -Environment homolog -Action list|create|revoke` chama `services/content-api/manage_keys.py`, que **nunca é implantado** (fora da lista do empacotador). `create` e `revoke` são dry-run sem `-Apply` e sem abrir conexão; a chave nova aparece **uma única vez** no terminal de quem roda (ou vai para a área de transferência com `-ToClipboard`, sem ser impressa); só o hash vai ao banco; `list` mostra metadados (id, nome, escopo, validade, revogada) e nunca o hash. A credencial do arquivo privado vira variável de ambiente só do processo filho e é removida no `finally`. A ferramenta recusa rodar se `CMS_SQL_DATABASE` não for o banco do ambiente pedido. A chave só cria rascunhos, sobe mídia e envia pacotes; nunca aprova. 6 testes novos (22 em `services/content-api`); eles pegaram um defeito meu: o dry-run do `revoke` abria a conexão antes de checar `-Apply` (corrigido).

Verificado: `list` contra o banco real de homolog, a partir desta máquina, respondeu "No agent keys." (credencial de runtime, esquema e permissão de leitura de `agent_keys` funcionando). Na máquina do proprietário falta o driver SQL (`python-tds`, `certifi`, `pyOpenSSL`): o script avisa e `-InstallDependencies` instala as versões **pinadas** (`pyOpenSSL` 26.x remove um método que o `python-tds` 1.17.1 usa; foi o que quebrou meu primeiro teste local).

**Primeira chave criada pelo proprietário** (2026-10-29, no próprio terminal, copiada para a área de transferência sem ser impressa): `bff4c2330d7b4b82`, nome `claude-homolog`, escopos banners, content e media, validade até 2026-11-28. Confirmada com `list`; a chave nunca passou pelo chat.

**Teste de fluxo completo em homolog (2026-10-29): 24/24 verificações passaram** contra a API implantada, com uma chave descartável de 1 dia (criada e revogada dentro do próprio processo, nunca exibida): health, `schema`, validação (aceita artigo bom; acusa fonte `http`), upload de imagem base64 (WebP em 4–8 s na primeira chamada), repetição idempotente devolve o mesmo registro, mesma `Idempotency-Key` com outro corpo dá 409, imagem por URL recusada com a lista de hosts vazia, rascunho de artigo e de banner, `status=approved` e campos de mídia protegidos recusados, link `javascript:` recusado, envio de pacote com `reviewUrl`, o agente lê o status do próprio pacote, e **não consegue aprovar, listar pacotes, promover nem usar identidade de admin forjada** (401), corpo de 400 KB recusado (413), todos os registros seguem rascunho no banco e **nenhum release foi criado** (6 → 6; os 6 existentes são de setembro). A trilha de auditoria mostrou só `create`, `update`, `submit` e `upload` para a chave de teste, nenhum `approve`. Um primeiro teste meu falhou por presumir que não havia releases; era erro do teste, corrigido.

Ferramenta reutilizável: `infra/azure/content-key.ps1 -Environment homolog -Action smoke -Apply` (`services/content-api/smoke_homolog.py`, testado em processo contra o código real da borda; recusa qualquer banco que não seja o de homolog; revoga a chave no `finally`). **Efeito colateral:** cada execução deixa rascunhos de teste e um pacote pendente no banco de homolog (a credencial de runtime não apaga); hoje são 2 pacotes pendentes de teste. Eles aparecerão na página de revisão quando ela existir. Chaves hoje: `claude-homolog` ativa; `teste-e2e` e `smoke-8611e044` revogadas.

**Ainda não feito:** página de revisão e DNS `ia.`/`revisao.`; `AGENT_MEDIA_HOSTS` continua vazio (a API recusa buscar imagens por URL; imagens só por base64); conectores OpenAPI/MCP para Claude, ChatGPT, Gemini e Grok; produção.

## API das IAs: adaptador e configuração preparados (2026-10-29; depois implantados, ver acima)

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
