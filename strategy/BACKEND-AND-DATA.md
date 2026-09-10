# Backend e dados — AnderZilla

Decisão de arquitetura, 10/09/2026. O objetivo é um hub divertido e recorrente de games, IA, gadgets e tecnologia, com monetização contextual e Karaca Points. Este documento especifica o backend a implementar; não declara API ou banco implantados. Código de referência transacional existe em `services/rewards` na branch de aplicação.

## Escolha para o primeiro piloto

Manter Next.js com export estático em Azure Static Web Apps Free, uma aplicação de homologação e outra de produção. Implementar **Azure Functions gerenciadas pelo SWA, Python 3.11, com Azure SQL Database na oferta gratuita**, um banco separado por ambiente. Toda operação privada passa por `/api`; artigos, imagens públicas e índices de busca continuam estáticos. O site editorial permanece navegável quando o banco estiver pausado.

A tabela atual de configuração aceita `python:3.11`. A página geral de Functions ainda enumera versões mais antigas; usar a tabela específica de runtime e validar um endpoint mínimo na homologação antes de portar o domínio. Não confundir suporte à linguagem com implantação já comprovada. [Configuração oficial](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration).

Functions gerenciadas fornecem integração `/api`, mas limitam-se a HTTP: não têm managed identity, referências Key Vault, Durable Functions ou triggers de timer. Portanto, o primeiro piloto usa operações administrativas manuais para publicação, agenda e despacho; não criar cron fictício. Credencial SQL de mínimo privilégio fica exclusivamente em application settings, separada por ambiente e rotacionável. [Capacidades oficiais](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions).

Escolher inicialmente o adaptador `python-tds`, com versão travada, TLS integral, CA confiável, `validate_host=True` e `enc_login_only=False`; ele evita depender de instalação de driver ODBC no ambiente gerenciado. Isso é uma escolha de implementação sujeita a teste real de conexão, não integração pronta. Nunca desabilitar validação de certificado para resolver erro de deploy. [Projeto do driver](https://github.com/denisenkom/pytds), [parâmetros TLS](https://python-tds.readthedocs.io/en/1.16.1/pytds.html).

O Free suporta APIs gerenciadas e provedores pré-configurados, mas não oferece SLA. A alternativa de anexar Function App própria pela integração SWA exige Standard; não introduzi-la silenciosamente no orçamento atual. Se o teste de driver/runtime falhar, manter o piloto sem pontos reais até resolver o adaptador. [Planos SWA](https://learn.microsoft.com/en-us/azure/static-web-apps/plans), [Functions próprias](https://learn.microsoft.com/en-us/azure/static-web-apps/functions-bring-your-own).

## Custo e disponibilidade

A oferta SQL consultada concede, por banco, 100.000 vCore-segundos mensais, 32 GB de dados e 32 GB de backup; até dez bancos elegíveis por assinatura. Confirmar elegibilidade e opções no portal antes de criar os dois bancos. Selecionar **Auto-pause the database until next month**, nunca continuar com cobrança adicional. O limite pode suspender carteira e resgates até o mês seguinte; não prometer disponibilidade contínua. A oferta documenta retenção PITR de sete dias nessa modalidade. [Oferta Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-offer?view=azuresql).

O teto informado é R$150/mês, ainda sem clareza sobre inclusão das assinaturas pessoais existentes. Nesta fase, nenhum recurso pago novo é necessário ou foi provisionado. Não projetar gratuitidade ilimitada: medir consumo real, fechar conexões ociosas, limitar consultas e responder indisponibilidade de forma honesta. Não consultar carteira a cada render ou cada scroll. Usar carregamento sob demanda e backoff, sem polling de manutenção que mantenha SQL desperto.

Produção com resgates exige comprovar capacidade, recuperação e verba de recompensas separada. Ao atingir limites, congelar novas concessões e reservas; preservar saldo e pedidos. Nunca voltar ao localStorage como saldo alternativo. Telemetria paga, email transacional, armazenamento privado e custos de distribuição serão avaliados antes de ativar, não presumidos incluídos no SWA.

## Fronteiras e estado autoritativo

| Função visual | Dados e comportamento de produção |
|---|---|
| Radar, categorias, busca, PT/EN | Conteúdo validado e versionado no Git; export público por idioma; busca local no índice publicado. Rebuild publica novidades, sem consultar SQL para cada artigo. |
| Mochila e interesses | Visitante pode salvar localmente; conta sincroniza bookmarks e preferências na API. Importar somente itens válidos após ação explícita, nunca saldo demo. |
| Quiz e passaporte | Questões públicas sem gabarito de missão; tentativa emitida pelo servidor com versão/expiração; resultado verificado no backend. Abrir artigo não comprova leitura. |
| Missões, carteira e extrato | Valores, recorrência, janela e evidência definidos no servidor; ledger imutável e saldo transacional. |
| Store Points e pedidos | Só produto financiado, disponível e elegível pode ativar; custo e termos congelados no pedido. Reserva de pontos e estoque é atômica. |
| Live e agenda | Eventos confirmados, fuso explícito, URL canônica de canal; status com fonte e validade. Sem confirmação recente, exibir desconhecido. Player externo somente após ação do visitante. |
| Afiliados, anúncios, patrocinadores | Aprovação, prazo, mercado, disclosure e destino obrigatório. Sem aprovação, link editorial oficial; slots vazios não fingem patrocínio. |
| Administração | Papéis editor, comercial e operador de recompensas separados; auditoria. Primeira versão pode usar publicação editorial via PR e revisão de pedidos via ferramentas restritas. |
| Métricas e consentimento | Eventos mínimos, finalidade explícita, retenção definida e separação de análise editorial e integridade de pontos. Não premiar clique em anúncio. |

RAG e ferramentas de IA são exclusivos da operação na branch documental; não integram o backend público nem recebem contas, endereços de entrega, tokens ou histórico individual. Revisões entre IAs não são prova de produto testado.

## Modelo de dados

IDs internos opacos; timestamps UTC; KP inteiros; versão em regras, ofertas e termos; índices por conta/data para paginação. Idioma não define país elegível.

| Agregado | Estrutura proposta e restrições |
|---|---|
| `accounts`, `identities` | Conta, estado, país declarado/verificado conforme regra; identidade única por ambiente + emissor + subject. Email não é chave de associação automática. |
| `preferences`, `bookmarks` | Taxonomias permitidas, idioma, conteúdo salvo; unique(account, content). Sem inserir conteúdo inexistente. |
| `content`, `translations`, `sources`, `taxonomies` | IDs estáveis, slug/idioma únicos, status editorial, autoria, fonte, data do fato e publicação; inicialmente manifestos Git, futura importação com mesmos IDs. |
| `quiz_versions`, `questions`, `attempts`, `answers` | Versão congelada, expiração, respostas privadas no servidor, resultado; unique(account, quiz version, occurrence) para missão. |
| `missions`, `completions` | Prêmio, janela, limite e verificador por versão; ocorrência produzida pelo servidor e unique(account, mission, version, occurrence). |
| `wallets`, `ledger`, `requests` | Available/reserved não negativos; ledger append-only; idempotency key por conta vinculada ao hash canônico de operação e payload. |
| `rewards`, `reward_versions`, `inventory` | Traduções, categoria, unidades financiadas, custo KP, região, termos de licença/entrega; versão publicada imutável e movimentação de estoque auditável. |
| `redemptions`, `delivery_private`, `audit`, `outbox` | Estado, snapshot de versão/custo/termos; dados de entrega separados e com acesso restrito; registro de despacho único para evitar dupla emissão. |
| `channels`, `events`, `live_observations` | Plataforma e canal permitidos, início/fim/UTC/timezone, cancelamento; observadoEm/expiraEm/fonte para status. |
| `offers`, `campaigns`, `placements` | Tipo editorial/afiliado/patrocínio, estado, destino permitido, disclosure PT/EN, vigência, região e evidência de aprovação; métricas reais separadas. |
| `consents`, `analytics_daily`, `security_events` | Versão/finalidade/instante de consentimento; agregados de uso sem juntar identidade publicitária com carteira. Retenção configurável e exclusão auditada. |

As tabelas além do núcleo de recompensas são especificação, não migrações já aplicadas. O schema SQLite atual usa um registro por produto para referência; o adaptador SQL deve introduzir versões imutáveis e inventário histórico antes de resgates reais. Endereços, códigos digitais e chaves nunca entram em HTML, catálogo público, Git ou logs.

## Transações e integração do núcleo

`services/rewards/core.py` prova concessão, reserva, cancelamento, consumo e reconciliação em SQLite. Não publica HTTP. `Principal` representa identidade previamente verificada; não pode ser construído com accountId/roles enviados pelo navegador. O verificador padrão rejeita toda concessão.

Para Azure SQL, portar explicitamente DDL, placeholders e controle transacional; não executar `schema.sql` SQLite como migração T-SQL. Usar transação serializável ou locks de atualização nas linhas de carteira/estoque, sempre na mesma ordem, restrições únicas e retries limitados para deadlock. Toda reserva grava estoque, saldo, pedido e idempotência juntos. Não calcular saldo no JavaScript e não usar arquivo SQLite no filesystem efêmero de Functions.

Estados: `pending_review -> fulfilling -> fulfilled`; `pending_review -> cancelled` devolve reserva e unidade uma vez. Depois de iniciar entrega, cancelamento automático é bloqueado: falha ou resultado incerto exige reconciliação manual. Operador registra motivo e evidência de entrega. Adaptador de despacho futuro usa outbox e chave única; repetir requisição não pode reenviar gift card.

## Contratos de API

Versionar `/api/v1`. Respostas privadas `Cache-Control: no-store`; páginas públicas podem usar cache. Paginação por cursor com tamanho máximo. Erros estruturados: code, mensagem localizada pelo cliente e correlationId, nunca stack trace/SQL.

| Rota | Regra |
|---|---|
| `GET /me`, `PATCH /me/preferences` | Identidade da sessão; schema de preferências com lista permitida. |
| `GET /bookmarks`, `PUT /bookmarks/{contentId}`, `DELETE /bookmarks/{contentId}` | Escopo da conta; PUT idempotente. |
| `GET /missions`, `POST /quizzes/{id}/attempts`, `POST /attempts/{id}/submit` | Servidor emite tentativa e valida dono/versão/prazo/respostas/limites. |
| `POST /missions/{id}/complete` | Referência de tentativa verificável e versão; valor ou ocorrência de prêmio nunca aceitos do cliente. Idempotency-Key obrigatório. |
| `GET /points/wallet`, `GET /points/ledger` | Apenas conta atual; saldo demo não importável. |
| `GET /rewards`, `POST /redemptions`, `GET /redemptions/{id}` | POST recebe rewardId/version + Idempotency-Key; backend verifica estoque, região, termos aceitos e saldo. |
| `GET /events`, `GET /live` | Só itens publicados e status ainda válido; cache curto, sem anunciar live por suposição. |
| `POST /admin/redemptions/{id}/transition` | Papel operador, transição permitida, motivo e auditoria. |
| `POST /admin/campaigns`, `POST /admin/events` | Papéis comerciais/editoriais; validação de URL, datas, disclosures e versão. |
| `POST /consents` | Registro de finalidade e versão; ausência de consentimento não bloqueia leitura editorial básica. |

HTTP 401 sem sessão, 403 sem papel, 404 para objeto privado alheio, 409 para versão/estoque/colisão de idempotência, 422 para payload inválido, 429 para limite e 503 para banco indisponível. Retries mantêm a mesma chave. Formulário comercial só exibe sucesso após persistência real; enquanto não existir API, usar contato confirmado, sem envio simulado.

## Autenticação e integrações

Começar com GitHub e Microsoft via autenticação pré-configurada do SWA. Frontend consulta `/.auth/me`; API resolve header injetado pela plataforma e aplica ownership/estado/papéis novamente. Esse header só é confiável atrás da integração gerenciada, nunca em servidor HTTP aberto. `userId` é específico do recurso SWA, portanto homologação e produção têm identidades e dados independentes. [Identidade SWA](https://learn.microsoft.com/en-us/azure/static-web-apps/user-information), [provedores](https://learn.microsoft.com/en-us/azure/static-web-apps/authentication-authorization).

Proteger todas as rotas privadas com allowedRoles; homolog exige `anderzilla_reviewer`. Administradores recebem papel por convite controlado e também autorização interna por operação. Verificar Origin e proteção CSRF nas mutações com cookie; não aceitar accountId como escopo. Limitar tamanho de corpo, tentativas por conta e taxa de submissão. Não considerar autenticação prova de pessoa única: piloto de recompensas pequeno, regras e revisão de abuso.

Integrações Xbox, Steam, Discord, Twitch, Google/YouTube, PlayStation/Nintendo e outras ficam para fase própria com APIs/termos/escopos verificados. Inicialmente mostrar links confirmados. Login Microsoft não prova Game Pass, acesso a biblioteca, identidade de gamertag ou propriedade de canal. Vinculação exige consentimento e prova da conta, não igualdade de nome/email. Não guardar senha de plataforma nem depender de scraping autenticado.

## Sequência de entrega e critérios

1. **Frontend e homolog:** migração Next componentizada, PT/EN, acessibilidade, builds; demo identificada e sem resgates reais.
2. **Spike privado:** runtime Python 3.11 + conexão TLS Azure SQL elegível; banco com autopause, credenciais restritas, teste de suspensão/retomada e custo observado. Sem concessão pública.
3. **Conta e sincronização:** sessão, preferências, mochila, consentimentos; testes de outra conta e CSRF. Conteúdo segue Git editorial.
4. **Carteira fechada:** portar domínio para SQL; repetir concorrência da última unidade, idempotência, janela de missão, saldo insuficiente, rollback, ledger reconciliado e restauração de backup. Remover todos os doubles de teste do caminho implantável.
5. **Piloto de resgates:** estoque e termos reais, simulação de entrega manual, orçamento de recompensas e suporte; só então ativar missões resgatáveis. Saldo demo permanece descartável.
6. **Operação comercial:** campanhas aprovadas e agenda; medir retorno, interesse editorial e conversão sem inventar receita. Automação e APIs externas entram quando justificadas por uso real.

No núcleo local, `python -m unittest discover -s services/rewards -v` passou **11 testes**: concorrência entre conexões, atomicidade sob falha injetada, replay, autorização, regiões/versões, janela, cancelamento/consumo e ledger imutável. Isso não substitui testes do adaptador Azure SQL, autenticação ou entrega. Aplicações Next tocadas exigem `npm run build`.
