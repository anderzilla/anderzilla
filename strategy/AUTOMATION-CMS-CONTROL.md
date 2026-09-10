# Controle de automações e serviços pelo CMS

Data: 2026-09-10. Estado: especificação de implementação; não representa serviço implantado ou integração autenticada. Complementa ADMIN-CMS-PLAN.md, BACKEND-AND-DATA.md e o plano de automação multicloud. Autor da análise: subagente Codex, com inspeção do código local. Nenhum outro provedor de IA foi consultado nesta subtarefa.

## 1. Base observada e lacunas

Inspecionados: apps/admin/src/lib/cms.ts, components/Control.tsx, services/cms/{core,api,function_app,storage}.py, schema.sql e serviços publisher. A aplicação tem cadastros editoriais, taxonomias, mídia, eventos, ofertas, afiliados, campanhas, missões e recompensas; revisões, auditoria, autorização por papéis e fila de releases. Há upload de imagens normalizadas WebP e metadados de vídeos externos. O endpoint atual transporta imagens pequenas em JSON/base64, com biblioteca inicial limitada; não serve para gravações de lives.

Relatórios atuais exibem contagens de cadastros e auditoria. O backend declara analyticsConnected=false e rewardsLive=false. Portanto ainda não existem relatórios conectados de receita/audiência, execução genérica de jobs, agendamento de automações, upload resumível de vídeos nem processamento de cortes por esses módulos. Código presente não comprova implantação ou funcionamento da nuvem. Os inventários contêm registros históricos conflitantes: revalidar acesso/billing antes da implantação, preservando a informação mais recente do proprietário sobre crédito Google como informação fornecida, não confirmação via API.

## 2. Fronteiras da arquitetura

- Azure permanece com portal estático, CMS, banco autoritativo e aprovação editorial. Não mover o portal nem alterar DNS para implementar o primeiro piloto.
- Cloud Run recebe tarefas delimitadas: coletar fontes autorizadas, verificar conectores, preparar rascunhos, processar mídia e produzir artefatos. Workers não recebem acesso direto ao banco CMS nem poder para publicar.
- Um dispatcher autenticado envia comandos duráveis do outbox Azure para o adaptador GCP. Pode começar como execução manual controlada; agendador gerenciado só após verificar plano/custo. O adaptador entrega tarefas assíncronas e registra recibos.
- Primeiro transporte de resultados: CMS busca a caixa de saída privada GCP com identidade de serviço. Isso evita abrir a API gerenciada SWA a callbacks externos. Evolução para callback exige gateway separado que valide identidade máquina; nunca confiar no header SWA fora da fronteira SWA.
- Artefatos grandes ficam em armazenamento de objetos GCP; metadados e referências imutáveis ficam no CMS. Só peças finais aprovadas são exportadas ao portal. Não replicar gravações inteiras entre nuvens.
- Chamadas externas pertencem a adaptadores determinísticos com APIs permitidas. LLM sugere; política no servidor autoriza. Prompts/fontes/RAG não mudam permissões, orçamento ou destinos.

## 3. Experiência administrativa

Adicionar seis áreas, sem substituir módulos editoriais existentes:

| Área | Ações e informações |
|---|---|
| Central de operações | Saúde por serviço, última verificação, fila, falhas acionáveis, gasto estimado separado do faturado, próximo agendamento, botão pausar novas execuções |
| Processos | Catálogo de processos, finalidade, origem/destino, status conectado/desconectado, parâmetros seguros, executar agora, agendar, pausar, histórico |
| Execuções | Filtros por período/processo/estado/mercado, etapas, progresso confirmado, correlação, tentativas, artefatos, erro compreensível, reprocessar ou cancelar |
| Fábrica de cortes | Enviar gravação, acompanhar upload, indicar trechos, revisar transcrição, ajustar legendas, comparar versões e aprovar exportação |
| Relatórios | Semanal, mensal e intervalo personalizado; comparação equivalente; métricas operacionais/editoriais/comerciais/SEO; exportação CSV e documento resumido |
| Conexões e fontes | Canal, conta confirmada, escopos, validade, quotas, última coleta, atraso, reconectar, pausar; fonte oficial/RSS/API e direitos de uso |

Toda tela deve ter estados carregando/vazio/sem acesso/desconectado/parcial/falha e data da informação. Nunca apresentar zero quando não há conector ou a coleta falhou. Preferir detalhe progressivo: ação principal clara e parâmetros avançados recolhidos. Teclado, foco após navegação, labels, mensagens live-region e contraste AA. Paginação no servidor, filtros compartilháveis sem tokens na URL. Ambiente homolog/produção sempre visível.

Execução manual abre uma prévia com entradas, saídas, modelo solicitado e fallback autorizado, limite de minutos/tokens/bytes, custo estimado e efeito externo. Rodar uma análise não autoriza publicar ou enviar mensagens. Revisões e aprovações têm versão: aprovação anterior perde validade após alterar texto, corte, destino ou disclosure.

## 4. Persistência proposta

Migrações aditivas no Azure SQL; manter registros editoriais existentes. SQLite pode continuar como adaptação de teste, nunca como prova de semântica SQL concorrente. Relacionamentos e unicidade críticos em tabelas próprias, não apenas documentos JSON.

| Tabela | Campos e invariantes principais |
|---|---|
| automation_processes | id, type allowlisted, version, status, config JSON validado, capability, environment, budgetPolicyId, createdBy; versões imutáveis |
| automation_schedules | processVersionId, timezone IANA, regra, nextRunAtUTC, enabled, missedRunPolicy; horário local explícito e teste de DST |
| automation_runs | id, processVersionId, trigger, requesterId, inputHash, idempotencyKey, state, correlationId, budgetReservation, createdAt/startedAt/finishedAt; unique(environment,requesterId,idempotencyKey) |
| automation_attempts | runId, step, attempt, leaseOwner, leaseExpiresAt, fencingToken, status, providerExecutionId, errorClass; unique(runId,step,attempt) |
| automation_outbox | eventId, aggregateId, schemaVersion, payloadRef/hash, availableAt, lease, attempts, deliveredAt; inserido na mesma transação do comando |
| automation_inbox | producerId,eventId,payloadHash,receivedAt,processedAt; chave composta única e rejeição de hash divergente |
| automation_artifacts | runId, objectRef, sha256, mediaType, size, sourceRef, rightsRef, modelVersion, reviewState; objetos imutáveis privados |
| media_upload_sessions | id, userId, objectKey, expiry, expectedMaxBytes, checksum, state; sessão vinculada a objeto/usuário/ambiente |
| media_derivatives | sourceAssetId, recipeVersion, trimStart/end, aspectRatio, captionAssetId, renderRunId, approvedRevision; vínculo da origem ao corte |
| integration_connections | provider, ownerRef, scopes, status, credentialRef, lastSuccessAt, freshnessPolicy; somente referência ao segredo |
| source_registry | URL/API allowlisted, license/rights, cadence, contentHash, lastFetchAt, language, market; proveniência obrigatória |
| metric_observations | source, metric, periodStart/endUTC, dimensionsHash, dimensionsJSON, unit, value, currency, observedAt, quality, sourceRecordId; unique(source,metric,period,dimensionsHash,sourceRecordId) conforme adaptador |
| report_runs | filters canônicos, timezone, queryVersion, asOf, completeness, artifactRef, requester, snapshotHash |
| budget_reservations | runId, currency, amountMinor, tokens/minutes/bytes caps, consumed, reconciledAt; reserva atômica |

Eventos/auditoria guardam ator humano ou service principal, motivo, ambiente e versões, sem conteúdo secreto. Retenção proposta: logs detalhados 30 dias, métricas agregadas 13 meses e uploads incompletos 24 horas; brutos de vídeo 7 dias após conclusão, com aviso e política configurável antes do envio. Alterar retenção exige explicação do efeito; preservar materiais sob revisão até a política definida, sem apagar silenciosamente. Minimizar identificadores de público; sem armazenar chat integral por padrão.

## 5. Contratos HTTP propostos

Todos os endpoints abaixo são novos. Estender o roteador CMS, com validação de schema e autorização no servidor. Prefixo administrativo /api/admin; não usar rotas públicas para comandos.

| Método e rota | Resultado |
|---|---|
| GET /automation/processes | Processos e capacidades reais por usuário |
| POST /automation/runs/preview | Valida entradas; estima limites sem efeitos externos |
| POST /automation/runs | Idempotency-Key + processVersion/input/limits; 202 com runId e Location |
| GET /automation/runs?from=&to=&cursor= | Lista paginada e filtros autorizados |
| GET /automation/runs/{id} | Estado, etapas, artefatos e erros sanitizados |
| POST /automation/runs/{id}/cancel | Cancelamento cooperativo; não afirmar interrupção imediata |
| POST /automation/runs/{id}/retry | Nova execução relacionada, limite de retries e nova autorização |
| PUT /automation/schedules/{id} | If-Match/version, configuração e revisão de custo |
| POST /media/uploads | Cria sessão de upload direta resumível, limitada e privada |
| POST /media/uploads/{id}/complete | Verifica objeto real, tamanho, checksum e tipo; fila de inspeção |
| POST /media/{id}/cuts | Intervalos/receita e limites; cria execução idempotente |
| POST /automation/artifacts/{id}/review | Aprovar/rejeitar versão exata com motivo |
| GET /reports?from=&to=&timezone=&groupBy= | Agregação com período e qualidade explícitos |
| POST /reports/exports | Exportação assíncrona privada com filtros imutáveis |
| GET /integrations/status | Saúde, última coleta e escopos; nunca tokens |

Erros estáveis: 401 sessão, 403 capacidade, 409 versão/chave divergente, 422 entrada, 429 quota e 503 dependência. Logs internos vinculados por correlationId; mensagens públicas não vazam stack ou provider token. Origem/CSRF validados para comandos por sessão. CORS restrito; URLs assinadas só via resposta autenticada e com TTL curto.

## 6. Semântica de execução e comunicação

Estados: queued -> dispatching -> running -> awaiting_review -> succeeded. failed/cancel_requested/cancelled e blocked são estados explícitos; retry cria tentativa ou execução derivada conforme efeito já produzido. Dispatch com lease não significa processamento concluído. Uma execução pode concluir sem publicação; publicação usa release separado.

Na mesma transação: validar permissão e versão, verificar quota, reservar orçamento, inserir run + outbox + auditoria. Dispatcher reclama evento por lease, envia eventId estável e persiste recibo. Falha após envio e antes do recibo pode duplicar entrega: inbox e efeitos idempotentes obrigatórios no consumidor. Não prometer exactly-once de transporte. Chave reutilizada com payload diferente é 409. Resultado de tentativa antiga não sobrescreve tentativa nova: validar fencingToken, estado e versão.

Envelope mínimo: eventId, type, schemaVersion, environment, aggregateId, correlationId, causationId, createdAt, expiresAt, payloadRef, payloadSha256. Producer autenticado deriva da credencial, não do JSON. Retry com backoff+jitter, limite 5 tentativas como padrão configurável e fila de falhas para revisão; 401/403/configuração e falhas determinísticas não recebem retry cego. Webhooks de plataformas exigem validação específica do provedor e replay protection antes de virar eventos internos.

Credenciais entre nuvens: priorizar federação de identidade com audiência/subject/issuer restritos após validar compatibilidade do runtime Azure escolhido; não afirmar que já existe. Se indisponível, implementação fica bloqueada para produção até método revisado, em vez de chave privada em CMS/Git. GCP usa projeto explícito e configuração anderzilla sob player.one@anderzilla.com. Service accounts distintas para dispatcher, processador e leitor de resultados; acesso mínimo por ambiente/bucket/prefixo.

## 7. Mídia e fábrica de cortes

Fluxo: criar sessão -> upload direto retomável -> confirmar bytes/checksum -> quarentena e inspeção -> extrair metadados -> transcrever se habilitado -> sugerir cortes -> escolher e ajustar -> renderizar -> revisar -> exportar. Upload não implica execução paga automática; política do processo explicita isso.

Validar magic bytes/container/codecs, duração, resolução, limite de tamanho, proprietário e direitos declarados. Nomes de arquivo não viram comandos; ffmpeg com argumentos estruturados, sem shell concatenado, limites de CPU/memória/tempo e entrada sem acesso arbitrário à rede. Importação por URL, se adicionada, bloqueia SSRF/redirecionamentos para rede privada e requer origem autorizada; MVP aceita upload próprio, não downloader universal de redes.

UI: progresso real de bytes, retomada, estimativa indicada como tal, player privado com scrub/teclado, faixa de início/fim, safe areas 9:16/1:1/16:9, editor de legendas PT/EN, revisão de nomes próprios, thumbnail, direitos da trilha, fonte e CTAs comerciais. Exportar MP4 + SRT/VTT + metadados. Cada derivado tem versão, checksum e origem. Publicação social depende de conector/permissão próprios e aprovação; nunca simular sucesso de publicação.

## 8. Relatórios confiáveis

Semanal: segunda 00h até próxima segunda; mensal: calendário local; personalizado: [início,fim) com timezone America/Sao_Paulo por padrão, persistência UTC. Mostrar datas exatas e comparação com intervalo anterior de igual duração ou calendário equivalente escolhido. Reconciliação de dados tardios gera nova versão do relatório, preservando as anteriores.

Grupos: operação (sucesso/falha/latência/fila/custo), produção (peças aprovadas, tempo de revisão, cortes aproveitados), comercial (cliques, conversões confirmadas, receita bruta, reembolsos, comissão e margem quando custo existir), SEO (impressões/cliques/CTR/posição da fonte e páginas com problemas), canais (métricas nativas com definição e janela).

Nenhuma soma de seguidores como pessoas únicas. CTR agregado = soma cliques / soma impressões, não média simples dos percentuais. Distinguir receita estimada/aprovada/paga; nunca atribuir venda só por clique. Moedas separadas até conversão com taxa/fonte/data informadas. Mercado br/intl/global separado do idioma. Exibir cobertura, atraso, origem, data da coleta, indisponível vs zero e comparação incompleta. Relatórios podem ser gerados manualmente e por agenda; envio por email/mensagem somente com destino e autorização específicos.

## 9. RBAC e segurança

Preservar papéis atuais admin/editor/commercial/rewards e adicionar capacidades finas, não promover todo operador a admin:

- admin: conexões, políticas de custo, agendas, interrupção global e aprovações de publicação.
- editor: processos editoriais e mídia; revisão de rascunhos próprios/permitidos; sem segredos ou relatório financeiro restrito.
- commercial: campanhas/ofertas e relatórios comerciais permitidos; não altera pontos nem publica sem capacidade de release.
- automation_operator (proposto): iniciar/repetir/cancelar apenas tipos permitidos; sem mudar credenciais ou limites máximos.
- analyst (proposto): leitura/exportação de agregados autorizados; sem dados pessoais ou mudanças.
- service principals: escopos por etapa e ambiente; nunca papéis humanos por header recebido.

Cada leitura de run/artifact/export valida ownership/escopo, inclusive URL assinada. Revisão editorial não concede acesso a entrega de recompensas. MFA e recuperação de proprietário devem ser verificadas no provedor de identidade, não inventadas pela interface. Segredos em cofre com rotação/revogação; logs redigidos. Kill switch pausa novos comandos e retries, mas sinaliza tarefas em execução e custos já incorridos.

## 10. SEO entre nuvens

Cloud Run prepara artefatos e avaliações; páginas indexáveis permanecem no domínio Azure canônico. Serviços internos não são conteúdo indexável. Não criar cópias públicas de artigos no domínio run.app. Gerador entrega títulos, descrição, transcrição, alt, fontes, idioma, autoria e sugestões de links como rascunhos. CMS valida slug, traduções existentes, canonical, hreflang, redirects, qualidade e schema compatível com o conteúdo visível antes do release.

SEO deve medir indexabilidade e qualidade real, sem prometer ranking por usar duas nuvens. Search Console e outras fontes exigem conexão verificada. Vídeos finais podem ter transcrição e página editorial própria; metadados de vídeo só quando player/thumbnail e dados exigidos existirem. Publicação permanece snapshot revisado -> build/validação -> homolog -> produção do mesmo artefato aprovado. Jobs SEO retornam issues para o CMS com severidade/evidência/correção sugerida, não alteram produção automaticamente.

## 11. Lotes de implementação e aceite

1. Contratos/migrações/RBAC: testes de outra conta, outra função, ambiente cruzado, chave divergente e reversibilidade da migração. Sem novos recursos pagos.
2. Catálogo e execução manual com worker local de tarefa inofensiva: provar outbox/inbox, crash antes/depois do envio, lease vencido, resultado atrasado, cancelamento e bloqueio por orçamento.
3. Um worker privado GCP em homolog após acesso verificado: testar identidade inválida, quota, perda de rede, limites e artefato privado. Só depois habilitar agenda limitada.
4. Upload/cortes: limite excedido, MIME falso, checksum divergente, retomada, expiração, acesso cruzado, interrupção de render e revisão invalidada por alteração. Medir custo em amostra curta antes de lives longas.
5. Relatórios: fixtures rotuladas apenas em teste, períodos/DST, dados tardios, zero vs ausente, moedas, deduplicação e autorização das exportações. Produção começa vazia até conectar fontes.
6. Conteúdo/SEO: rascunho vindo de worker, revisão humana, metadados consistentes, build apps tocadas, homolog privado e verificação de publicação sem duplicatas indexáveis.

Definition of done por lote: contrato versionado, implementação revisada por agente independente, testes de comportamento e falhas, evidência de build das apps tocadas, rollback, custo observado e capacidades habilitadas refletidas pelo servidor no CMS. Planejamento e mocks não habilitam botão que afirme serviço conectado. Responsáveis multi-IA devem registrar o provedor efetivamente executado, arquivos delegados e evidência da revisão.
