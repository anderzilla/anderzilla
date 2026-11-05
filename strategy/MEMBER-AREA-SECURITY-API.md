# Área do jogador — autorização, dados e contratos propostos

05/11/2026. **Especificação futura**, a reconciliar com código antes de implantar. Não ativar /api/points legado pelo simples encaminhamento do router Clerk. [Produto](MEMBER-AREA.md), [UX](MEMBER-AREA-UX.md), [aceite](../operations/MEMBER-AREA-DELIVERY.md).

## 1. Matriz de autoridade

| Recurso / comando | Visitante | Clerk verificado sem cadastro | Membro completo ativo | Suspenso/excluído | Operador |
|---|---|---|---|---|---|
| Conteúdo editorial marcado público | Sim | Sim | Sim | Público continua público | Conforme publicação |
| Capabilities genéricas / entrada | Sim | Sim | Sim | Sem dados pessoais | Sem autoridade extra |
| Onboarding próprio | Login primeiro | Sim | Idempotente, sem recriar | Não | Migração via procedimento separado |
| Painel/dados próprios/Radar personalizado | Não | Não | Sim | Não | Sem acesso por ser operador editorial |
| Mochila/interesses/exploração | Não | Não | Próprios | Não | Sem acesso transversal padrão |
| Carteira/extrato/missões/tentativa/claim | Não | Não | Próprios, feature e elegibilidade válidas | Não | Correções por papel específico e auditoria |
| Alterar saldo/regras/estoque/moderação | Não | Não | Não | Não | Papel separado; nenhum endpoint de membro |
| Conteúdo membro/assinado/comprado futuro | Não | Não | Somente direito específico válido | Não | Acesso administrativo explícito, não implícito |
| Webhook Clerk | Assinatura Svix, não sessão | Igual | Igual | Igual | Credencial de webhook não é privilégio de membro |

Papel anderzilla_reviewer abre ambiente de homologação, não o cadastro de outra pessoa, painel operacional ou carteira. Não aceitar flag isAdmin/plan/award do navegador ou public_metadata Clerk como autoridade. Content type e exact Origin nas mutações somam proteção, mas não substituem autenticação e autorização.

## 2. Middleware/serviço de acesso obrigatório

Ordem: limitar corpo/validar contrato → verificar JWT RS256, emissor, tempo e azp → confirmar sessão Clerk ativa/e-mail confirmado → buscar conta local e vínculo único → exigir ativo/adulto/cadastro completo → checar feature e direito ao recurso → executar operação escopada por account_id derivado do servidor. Nunca executar consulta pessoal antes de conhecer o dono.

Onboarding, capabilities, ready e webhook são exceções explícitas e mínimas. GET /me anônimo pode retornar apenas account:null; nenhum outro dado pessoal. Suspenso/excluído não deve cair no mesmo fluxo de “perfil ainda não criado”. Cadastro não cria privilégio editorial nem direito pago.

O cabeçalho X-AnderZilla-Authorization transporta bearer validado; não é prova por si. SWA pode substituir Authorization; não confiar no bearer da plataforma como identidade Clerk. Homolog same-origin /api; produção Function App com CORS exato; validar preflight real no navegador. Sem cookie de conta próprio e sem token em URL.

Respostas:401 precisa entrar;403 cadastro incompleto/conta bloqueada/sem elegibilidade conforme contexto;404 recurso inexistente **ou de outra conta**;409 conflito de versão/idempotência;410 tentativa/pendência expirada;422 validação;429 limite com Retry-After;503 indisponibilidade/feature temporariamente fechada. Mapear a códigos internos estáveis e copy humanizada; não refletir mensagens de SQL/Clerk nem revelar colisão de CPF/e-mail.

## 3. Exportação estática, cache e navegação

- HTML/out, RSC/JSON de build, sitemap, OpenGraph, índices de busca, feed, screenshots de CI e manifests não contêm perfil, preferências, IDs de sessão, KP, tentativas, gabaritos privados ou URLs assinadas. Rotas privadas têm metadata genérica e noindex; noindex não é controle de acesso.
- Shell estático200 não concede acesso. Não incluir API keys secretas nem consultar contas reais no build. Chave pública Clerk pode estar no bundle; segredo e HMAC nunca.
- API privada Cache-Control:no-store; frontend credentials:omit, cache:no-store. Sem CDN/revalidação compartilhada para dados pessoais; Vary:Origin sozinho não torna cache seguro. Não usar apenas uma chave “wallet” global no cliente.
- Cada request e cache em memória usa subject/account+sessionEpoch+feature/version. Em logout/troca/suspensão/exclusão, aumentar epoch, cancelar requests e descartar qualquer resposta de epoch anterior. Mesma regra para paginação, PATCH otimista, exportação e claim. Backend sempre decide autorização independentemente da UI.
- Limpar DOM, store, caches, timers, overlays e URLs Blob de exportação ao encerrar acesso. Não manter dados de membro em localStorage/sessionStorage/IndexedDB, service worker, cache offline ou analytics. Pendência de missão fica no servidor com dono, não token sem dono em sessionStorage.
- Multiabas: sinal de invalidação sem dados pessoais (BroadcastChannel ou equivalente), revalidar ao foco/pageshow/bfcache. Nenhum saldo/perfil de A pode aparecer na entrada de B. Operações públicas seguem funcionando sem SQL quando não precisam de conta.
- Reautenticação incerta → fechar dados privados. Na falha de atualização comum dentro de sessão ainda confirmada, rotular “não atualizado” apenas se política de sessão permitir; nunca mostrar snapshot de sessão antiga como saldo atual.

## 4. Fronteira de conteúdo público e restrito

Modelo proposto de metadados: visibility=public|member|entitled, publicationStatus, mercado/idioma; entitled inclui política de direitos separada (site_plan, purchase, live_channel) com janela de validade. Nesta etapa somente acervo público já publicado é recomendado; tipos privados futuros permanecem sem publicação até haver pipeline privado.

Filtros de Radar, Mochila, Exploração e dashboard aplicam publicação+permissão na API **antes** de devolver título, resumo, imagem, slug e contagens. IDs privados não podem entrar em índice público, HTML oculto ou preload. Não servir artigo restrito como arquivo estático público e tentar escondê-lo com botão de login. Não usar URL difícil como barreira. Imagem, PDF, player e mídia privados precisam da mesma política; assinatura curta só após autorização quando esses produtos existirem.

Compartilhar uma notícia pública não compartilha Radar, interesses ou histórico. Compartilhamento de conteúdo privado, se vier a existir, retorna gate sem metadados sensíveis. E-mails/notificações não incluem conteúdo restrito para conta sem direito atual. Sem endpoints “perfil público” ou ranking por padrão.

## 5. Modelo de dados alvo e reconciliação

Reutilizar accounts/managed_identities/managed_profiles como identidade, sem outro cadastro nem carteira independente. Há preferências JSON e wallets/ledger no domínio identity, e referência separada em services/rewards; reconciliar invariantes em uma fonte persistente, não operar dois saldos.

| Agregado | Requisitos propostos |
|---|---|
| Interesses | account_id, category_id válido, versão do conjunto, updated_at. Unicidade por conta/categoria; ETag/If-Match ou versão equivalente. |
| Mochila | account_id, discovery_id, saved_at; chave única composta e cursor estável. Modelo relacional recomendado para não substituir lista inteira concorrente. |
| Exploração | account_id, discovery_id, first_opened_at, last_opened_at, historyGeneration; evento deduplicado e versão por remoção; índice por conta/data. Limpar incrementa geração atomicamente; rejeitar evento de geração anterior, não recriar histórico por atraso de rede. |
| Dashboard | Projeção limitada de dados próprios; estados por bloco, sem gravar outra cópia de saldo. |
| Missão | Identificador estável, versão, occurrenceKey, estado, elegibilidade, evidência, janela, limites e awardKP aprovado. Publicação versionada não permite ganhar de novo sem regra explícita. |
| Tentativa/evidência | account_id, mission_id/version/occurrence, attempt_id aleatório, expiração, estado e resultado. Gabarito só servidor. Constraint por regra de concorrência; limite de tentativas configurado. |
| Pending claim | Dono, evidência verificada, validade, status e receipt_id. Não aceitar principal=None; ID opaco não é autorização. |
| Cobertura/quotas | Envelope por campanha/ciclo e limite por conta. Reserva interna idempotente ao validar evidência elegível, expiração e consumo/liberação únicos. Não é saldo KP do usuário; não publicar valores internos de cobertura. |
| Wallet/ledger | KP inteiros, disponível/reservado não negativos; lançamento imutável; índice/constraint de deduplicação. Saldo calculado/atualizado sob transação, nunca no cliente. |
| Operação idempotente | account_id+tipo+key únicos, hash do payload, estado e resultado mínimo. Mesma chave/outro payload →409; mesma chave/mesmo payload →mesmo efeito e resultado. |
| Sanção/auditoria | Ator, ação, motivo e horário; retenção mínima separada de preferências apagáveis. Sem CPF completo, token, resposta secreta ou payload pessoal integral nos logs. |

Migração: export/backup controlado → schema aditivo e backfill por conta → comparar contagens/invariantes → canário → desligar escrita de listas legadas → adaptar export/exclusão → retirar coluna/contrato somente em migração própria. Não migrar salvos/interesses/exploração anônimos por suposição, nem saldo demo. Limite1000 atual exige paginação e política de capacidade, não erro surpresa no1001º item.

## 6. API alvo, sempre derivando dono no servidor

Prefixo /api, sem accountId nos comandos de membro. Rotas abaixo são propostas; não estão todas implementadas. Perfil não deve continuar sendo endpoint genérico para substituir coleções inteiras depois da migração.

| Método e rota | Entrada/saída mínima | Proteção |
|---|---|---|
| GET /member/dashboard | Resumos e estado por bloco, versão/asOf, sem segredos | Membro; sem resultado agregado de outra conta |
| GET /member/radar?cursor&category | IDs/metadados públicos autorizados, próximo cursor; usa interesses server-side | Membro; cursor opaco vinculado a filtro/versão |
| GET /member/interests | Categorias escolhidas e versão | Próprios |
| PUT /member/interests | categoryIds+expectedVersion | Lista válida, limite, conflito409; gravação atômica |
| GET /member/backpack?cursor | Itens permitidos + placeholders mínimos de indisponíveis | Próprios; ordenação estável |
| PUT /member/backpack/{discoveryId} | Salvar, sem duplicar; estado confirmado | Recurso autorizado; idempotente |
| DELETE /member/backpack/{discoveryId} | Remover se existir | Próprios; idempotente; Content-Type/Origin definidos |
| GET /member/exploration?cursor | Histórico privado e progresso confirmado | Próprios |
| POST /member/exploration/events | discoveryId+tipo permitido+eventId+historyGeneration; data final server-side | Recurso autorizado; replay sem inflar; geração antiga rejeitada; sem leitura alegada |
| DELETE /member/exploration/{discoveryId} | Remover histórico do item | Próprios |
| POST /member/exploration/clear | Confirmação + versão, limpa somente escopo explicado | Transação; não apaga prova mínima de crédito |
| GET /points/wallet | available,reserved,asOf,version,programState | Membro + programa habilitado |
| GET /points/ledger?cursor | Lançamentos próprios e cursor | Mesmo gate, sem IDs de terceiros |
| GET /points/missions | Regras publicadas, estado próprio, tentativa atual e pendência recuperável | Membro, feature e elegibilidade; nenhum registro de terceiro |
| GET /points/challenges/{attemptId} | Tentativa própria, prazo, estado, resultado enviado/pendência ou recibo | Retomada após reload/login; não devolve gabarito nem rascunho não enviado |
| POST /points/challenge | missionId/version → tentativa e prazo | Dono obrigatório desde início; idempotency key |
| POST /points/evidence | attemptId+respostas permitidas → estado/pendência própria | Corrigir contrato legado; assinatura de evidência não substitui dono |
| POST /points/pending/claim | pendingId/token+Idempotency-Key → receipt e wallet | Validar dono, validade, regra e não concedido |
| GET /points/operations/{operationId} | Resultado/receipt atual de operação própria | Recuperar timeout sem repetir efeito |
| GET /points/operation-status?type={allowedType} | Idempotency-Key em cabeçalho → operação própria ou estado não iniciado | Chave conhecida antes do POST permite consulta mesmo se operationId nunca chegou. Não revelar existência em outra conta. |

Atualizar CORS para PUT/DELETE e Idempotency-Key/If-Match caso usados; teste navegador real, não só resposta204. Preferir consistência com contrato interno existente ao implementar sem expor simultaneamente endpoints legados inseguros. Feature desativada não aceita mutação mesmo com rota antiga.

## 7. Transação de missão e carteira

1. Verificar membro e feature em **todas** as etapas, inclusive listas, desafio, evidência, pendência e consulta de resultado. Não criar tentativa anônima nem permitir transferência entre contas.
2. Servidor emite tentativa com regra/ocorrência e horário; cliente não escolhe KP, janela ou aprovação. Limitar desafios/evidências e proteger contra automação sem CAPTCHA obrigatório em todo login.
3. Validar respostas/evidência atual contra versão congelada e regra de pausas. Expiração e limitação usam relógio servidor. Ao gerar pendência elegível, reservar envelope global/ciclo e quota individual atomicamente, com prazo e efeito único. Sem cobertura, não produzir estado que prometa KP: informar indisponibilidade conforme regra antes de nova participação. Nunca premiar publicidade, mero scroll, tempo declarado ou abrir uma notícia.
4. Claim atômico: verificar pendência/dono/estado → lock/constraint de ocorrência → consumir reserva de cobertura/limites individuais e globais → inserir completion+ledger → atualizar wallet → marcar pendência consumida → registrar receipt. Commit único. Falha rollback completo. Não conceder acima da cobertura por duas contas agindo juntas. Expirar/cancelar pendência libera reserva uma única vez; consumo e liberação são mutuamente exclusivos. Limpeza de expirados precisa de caminho durável implementado (operação oportunista limitada e procedimento de operador, ou worker aprovado), não timer presumido.
5. Resposta perdida: consulta operação ou retry **mesma chave** devolve recibo; concorrência duplica zero efeitos. Mesma ocorrência em outra chave também não duplica crédito. Expiração depois do commit não desfaz crédito confirmado.
6. Estados do programa: active; new_activity_paused (não iniciar novas tentativas; permitir confirmação já coberta e válida); maintenance (mutações indisponíveis temporariamente, sem converter em erro de elegibilidade); closed (sem nova participação, com procedimento explícito para pendências anteriores). Política de extensão de prazo/revisão durante manutenção deve ser versionada e publicada antes de ativar. Bloqueio de segurança/conta sempre prevalece; reserva não concede acesso. Rollback técnico não pode apagar ledger confirmado. Correção por lançamento compensatório auditado.
7. Futuro resgate: reservar saldo+estoque atômicos, entregar uma vez, cancelar/devolver uma vez, estados de suporte auditados. Serviços externos por outbox/inbox ou mecanismo durável equivalente; não prometer worker/timer já instalado.

Retomada: em novo login/reload, listar estado próprio de missões e recuperar tentativa/pendência/recibo pelo servidor, sem token persistente no navegador. Após timeout no POST, consultar pela mesma chave conhecida antes do envio; se a página perdeu essa chave, GET da tentativa e estado próprio encontra o resultado. Quando não há operação iniciada, só repetir segundo a mesma regra/ocorrência, ainda sujeita à constraint de unicidade.

## 8. Privacidade, operação e encerramento

- Exportar inclui novas coleções próprias e extrato, mascarando CPF; nunca evidência de outra pessoa, chaves/tokens ou gabarito reutilizável. Limitar export e exigir sessão atual. Cancelar resposta de export se identidade mudar.
- Exclusão inclui interesses/mochila/exploração/avatar, tentativa e pendência conforme finalidade; revoga sessões e limpa UI. Antes da exclusão, explicar tratamento de saldo/reserva/pedido real segundo política ainda a aprovar; não apagar ledger/auditoria cegamente nem confiscar saldo por falha de sistema. Catálogo real permanece bloqueado enquanto esse ciclo não estiver definido.
- Conta suspensa: rejeitar novos comandos e consultas pessoais; operador restrito pode revisar e corrigir. Nenhum banner promete banimento automático infalível ou vazamento de motivo/dados de terceiros.
- Atendimento mostra referência opaca de operação e caminho privado de ajuda; não pedir CPF por URL pública/comentário. O canal público confirmado é player.one@anderzilla.com; coletar apenas o necessário, sem envio automático de dados.
- Logs/observabilidade: IDs opacos, latência/status e motivo técnico classificado, sem bearer, CPF, respostas de quiz, avatar dataURI, preferências ou payload integral. Retenção por finalidade precisa de decisão operacional documentada antes do lançamento das coleções novas; sugerir histórico visível limitado e limpeza voluntária, sem inventar prazo legal.
- Banco pausado/limite: backoff limitado e UX por bloco; sem polling contínuo para manter recurso desperto. Não criar serviço pago para cumprir este plano. Monitorar integridade sem coletar dados privados em RAG/IA.
