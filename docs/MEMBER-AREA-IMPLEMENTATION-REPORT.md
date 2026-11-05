# Relatório de Implementação — Área Autenticada do Jogador e Fonte Única de Carteira KP

- **Data**: 2026-11-05
- **Repositório de código**: `G:/AnderZilla`
- **Branch de implementação**: `codex/member-area-antigravity`
- **Commit base da branch**: `3e7d74884c0b05f1793c0ea3555077c18c569fd5` (`codex/registration-phase1-20261104`)
- **Documentação canônica consultada**: `G:/AnderZilla-docs` (`codex/anderzilla-docs`, commit `c195957330233ca17b005c4ecd65b84c86bfc139`, descendente de `4e213a2350bbb2ff09a03e2a0d5205f30f5fe337` registrado em `.anderzilla-docs-ref`)
- **Status**: Implementação concluída nos 5 lotes, validada por build estático (`npm --prefix apps/web run build`), suíte automatizada Python (`83` testes em `services/identity`) e verificação HTTP E2E loopback (`127.0.0.1:4173`). Pronta para validação independente pelo Codex.

---

## 1. Resumo Executivo

Foi implementada integralmente a **Área Autenticada do Jogador** (`/pt/conta/*` e `/en/conta/*`) e a **Fonte Única da Verdade para Karaca Points (KP)** do AnderZilla, seguindo os documentos canônicos `product/MEMBER-AREA.md`, `product/MEMBER-AREA-UX.md`, `operations/MEMBER-AREA-SECURITY-API.md`, `operations/MEMBER-AREA-DELIVERY.md` e `product/KARACA-POINTS.md`:

1. **Separação estrita entre visitante e membro verificado**:
   - Visitantes veem apenas o CTA `Entrar` / `Sign in` no cabeçalho, sem avatar próprio nem contadores pessoais falsos.
   - O progresso local de visitante (`localStorage` de favoritos, aberturas, interesses e `claims` locais) foi eliminado da experiência de membro e é higienizado automaticamente via `purgeLegacyVisitorStorage()`.
   - Ações de membro acionadas por visitantes (como guardar uma descoberta em página de artigo) registram uma intenção pós-login sanitizada (`savePostLoginIntent` / `consumePostLoginIntent`), exigindo confirmação explícita pós-autenticação antes de mutar dados da conta.
2. **Cabeçalho autenticado e Navegação da Conta (`/pt/conta/*` e `/en/conta/*`)**:
   - Membros verificados visualizam no cabeçalho o atalho `Seu Radar`, o chip de `KP` (`{available} KP` quando ativo, `KP —` quando indisponível/carregando — nunca `0 KP` falso — ou link neutro `Karaca Points` quando desativado) e o botão de disclosure acessível (`aria-expanded`, `aria-controls="member-navigation-disclosure"`, fechamento por `Escape` com retorno de foco ao gatilho, sem `role="menu"` incorreto) com os 10 itens canônicos.
   - Todas as rotas `/pt/conta/*`, `/en/conta/*` e `/account/` são exportadas estaticamente com `robots: noindex, nofollow`, headers `Cache-Control: no-store, max-age=0, must-revalidate` e `X-Robots-Tag: noindex, nofollow` em `staticwebapp.config.json`, exclusão de `sitemap.xml` e `Disallow` explícito em `robots.txt`.
3. **Painel do Jogador (6 blocos), Mochila, Interesses, Seu Radar e Exploração**:
   - `GET /api/member/dashboard` consolida `Seu Radar`, `KP e Carteira`, `Mochila`, `Próxima missão`, `Exploração` e `Seus interesses`.
   - `PUT /api/member/interests` usa controle de concorrência otimista (`expectedVersion` -> `409 interests_conflict` se outra aba alterou antes) e aceita `0..N` categorias válidas.
   - `GET /api/member/radar` retorna a união das categorias salvas ordenada da nota mais nova para a mais antiga, suportando filtro temporário (`?category=...`) sem alterar os interesses persistidos.
   - `GET/PUT/DELETE /api/member/backpack` oferece paginação determinística por cursor composto `(saved_at DESC, discovery_id ASC)` testada para mais de `1.000` itens, desfazer remoção e placeholder seguro (`available: false`, sem título/resumo/slug privado) para itens despublicados ou sem entitlement.
   - `GET/POST/DELETE /api/member/exploration` registra leitura deduplicada por `(account_id, discovery_id)`, concede `0 KP`, suporta remoção individual e limpeza total atômica com incremento de `exploration_generation` e tombstones que rejeitam eventos atrasados em trânsito (`409 stale_exploration_event`).
4. **Fonte Única de Carteira KP e Missões Transacionais com Cobertura**:
   - Eliminada a dualidade entre `services/identity/core.py` e `services/identity/clerk_service.py`: toda operação de carteira, extrato e missão oficial passa pela mesma conta verificada (`accounts.id`), `wallets` e `point_ledger`.
   - O fluxo de missão (`POST /api/points/challenge` -> `POST /api/points/evidence` -> `POST /api/points/pending/claim`) valida orçamento de campanha (`mission_campaigns`), reserva orçamento na aprovação da evidência, exige `Idempotency-Key` no `claim` (`409 idempotency_conflict` para payload divergente com a mesma chave), grava `mission_completions`, `mission_receipts`, `point_ledger` e `wallets` na mesma transação atômica e permite recuperação de estado pré-`operationId` via `GET /api/points/operation-status?type=claim`.

---

## 2. Arquivos Criados e Modificados por Lote

### Lote 1 — Guarda de Membro, Sessão, Cabeçalho, Painel do Jogador e Rotas `/conta`
- `apps/web/src/components/account/AccountProvider.tsx` *(modificado)*
- `apps/web/src/components/account/AccountUI.tsx` *(modificado)*
- `apps/web/src/components/account/MemberArea.tsx` *(criado)*
- `apps/web/src/components/account/account.css` *(modificado)*
- `apps/web/src/components/hub/Hub.tsx` *(modificado)*
- `apps/web/src/components/hub/Primitives.tsx` *(modificado)*
- `apps/web/src/app/[lang]/conta/routeHelper.ts` *(criado)*
- `apps/web/src/app/[lang]/conta/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/radar/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/perfil/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/mochila/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/interesses/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/exploracao/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/kp/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/carteira/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/missoes/page.tsx` *(criado)*
- `apps/web/src/app/[lang]/conta/missoes/[id]/page.tsx` *(criado)*
- `apps/web/src/app/account/page.tsx` *(criado)*
- `apps/web/src/app/robots.ts` *(modificado)*
- `apps/web/public/staticwebapp.config.json` *(modificado)*

### Lote 2 — Interesses, Mochila, Seu Radar e Fronteira de Visibilidade Editorial
- `services/identity/catalog.py` *(criado)*
- `services/identity/catalog_manifest.json` *(criado)*
- `apps/web/src/components/hub/HubProvider.tsx` *(modificado)*
- `apps/web/src/components/hub/ArticleMemberBar.tsx` *(criado)*
- `apps/web/src/app/[lang]/[section]/[slug]/page.tsx` *(modificado)*

### Lote 3 — Histórico de Exploração Confirmado, Geração e Limpeza Atômica
- `services/identity/schema.sql` *(modificado)*
- `services/identity/schema.azure.sql` *(modificado)*
- `services/identity/runtime-permissions.azure.sql` *(modificado)*
- `services/identity/migrations/002_member_area_additive.azure.sql` *(criado)*
- `services/identity/migrations/002_member_area_rollback.azure.sql` *(criado)*
- `services/identity/storage.py` *(modificado)*

### Lote 4 — Missões Transacionais, Cobertura KP e Fonte Única de Carteira
- `services/identity/core.py` *(modificado)*
- `services/identity/api.py` *(modificado)*
- `services/identity/member_service.py` *(criado)*
- `services/identity/clerk_service.py` *(modificado)*
- `services/identity/clerk_api.py` *(modificado)*
- `services/identity/function_app.py` *(modificado)*
- `apps/web/src/components/account/OfficialMissions.tsx` *(modificado)*
- `apps/web/src/components/hub/Rewards.tsx` *(modificado)*

### Lote 5 — Suíte Adversarial `A01–O04`, Reconciliação de Operador e Relatório Final
- `services/identity/managed_operator.py` *(modificado)*
- `services/identity/test_identity.py` *(modificado)*
- `services/identity/test_clerk.py` *(modificado)*
- `services/identity/test_function_app.py` *(modificado)*
- `services/identity/test_member_area.py` *(criado)*
- `infra/azure/identity-deploy.ps1` *(modificado)*
- `scripts/member_area_local_server.py` *(criado)*
- `docs/MEMBER-AREA-IMPLEMENTATION-REPORT.md` *(criado)*

---

## 3. Endpoints e Contratos Implementados

Todos os endpoints de `/api/member/*` e `/api/points/*` exigem:
- Verificação de origem (`Origin` na allowlist configurada)
- JWT Clerk válido (`Authorization` ou `X-AnderZilla-Authorization: Bearer <token>`)
- Conta local existente com `status = 'active'`, `email_verified = 1`, `birth_date` adulto (`18+`), `cpf_hmac` vinculado e `terms_version` / `privacy_version` vigentes (`require_member`)
- Respostas sempre com `Cache-Control: private, no-store, max-age=0` e `Vary: Origin, Authorization, X-AnderZilla-Authorization`
- Rejeição explícita (`422 invalid_fields`) de campos de autoridade/privilégio enviados pelo cliente (`role`, `isAdmin`, `plan`, `entitlements`, `award`, `balance`, `cpf`, `birthDate`, `accountId` etc.)

| Método e Rota | Contrato Resumido |
|---|---|
| `GET /api/member/dashboard` | Retorna os 6 blocos do Painel do Jogador (`radar`, `wallet`, `backpack`, `nextMission`, `exploration`, `interests`) e `greetingName`. |
| `GET /api/member/radar` | Retorna `items` filtrados pela união de interesses salvos (ou `?category=` temporário sem mutar interesses), ordenados do mais recente ao mais antigo, `declaredInterests`, `temporaryFilterOutsideInterests`, `nextCursor`. |
| `GET /api/member/interests` | Retorna `interests` (`categoryIds`), `version` e `updatedAt`. |
| `PUT /api/member/interests` | Valida `expectedVersion` (`409 interests_conflict` se divergente), atualiza categorias (`0..N`), incrementa `interests_version` e grava auditoria. |
| `GET /api/member/backpack` | Lista itens salvos paginados por cursor composto `(saved_at DESC, discovery_id ASC)` (`limit` até `50`, `cursor` validado com `422 invalid_cursor`). Projetados via `catalog.py`: itens despublicados ou sem entitlement retornam `{discoveryId, savedAt, available: false}` sem título/resumo/slug. |
| `PUT /api/member/backpack/{discoveryId}` | Salva item publicado/elegível de forma idempotente (`404 content_unavailable` se rascunho/inexistente/sem entitlement). |
| `DELETE /api/member/backpack/{discoveryId}` | Remove item da mochila de forma idempotente (inclusive itens que se tornaram indisponíveis). |
| `GET /api/member/exploration` | Retorna `items` abertos, `territoriesExplored`, `territoriesTotal`, `totalOpened`, `historyGeneration` e `nextCursor`. |
| `POST /api/member/exploration/events` | Registra abertura confirmada deduplicada por `(account_id, discovery_id)`. Rejeita `historyGeneration` antigo ou anterior a tombstone com `409 stale_exploration_event`. Retorna `awardedKP: 0`. |
| `DELETE /api/member/exploration/{discoveryId}` | Remove item do histórico e registra tombstone para impedir reaparecimento por evento atrasado. |
| `POST /api/member/exploration/clear` | Limpa `member_exploration`, grava tombstone global e incrementa `exploration_generation` atomicamente sem afetar mochila, interesses ou KP. |
| `GET /api/points/wallet` | Retorna `programStatus`, `available`, `reserved`, `lifetimeEarned`, `pendingConfirmationKP`, `pendingClaims` e `entries` recentes da carteira única. |
| `GET /api/points/ledger` | Lista extrato auditável paginado por cursor (`?limit=&cursor=&reason=`). |
| `GET /api/points/missions` | Lista missões oficiais com `programStatus`, `eligibility`, `activeAttempt`, `pendingClaim` e `receipt` sem expor gabaritos (`correctOption`). |
| `POST /api/points/challenge` | Inicia ou retoma tentativa oficial (`mission_attempts`), respeitando `programState` (`409 program_paused`, `503` em `maintenance`) e orçamento de campanha (`409 reward_capacity`). |
| `GET /api/points/challenges/{attemptId}` | Recupera estado da tentativa do próprio jogador (`404` para tentativa de outra conta). |
| `POST /api/points/evidence` | Valida evidência no servidor, reserva KP atomicamente em `mission_campaigns.reserved_kp` (`409 reward_capacity` se esgotado) e emite `pendingToken` com validade. |
| `POST /api/points/pending/claim` | Exige `Idempotency-Key`, valida `pendingToken`, consome reserva da campanha e grava `mission_completions`, `mission_receipts`, `point_ledger` e `wallets` na mesma transação (`409 idempotency_conflict` se mesma chave com payload diferente; `410 claim_expired` se expirado). |
| `GET /api/points/operations/{operationId}` | Consulta operação idempotente pelo `operationId` (`404` se pertencer a outra conta). |
| `GET /api/points/operation-status` | Recupera resultado de `claim` usando `Idempotency-Key` + `?type=claim` quando a resposta original caiu antes do cliente receber `operationId`. |

---

## 4. Migrações SQL Preparadas e Status de Execução

- **Arquivos preparados no repositório**:
  - `services/identity/schema.sql` (SQLite local/testes)
  - `services/identity/schema.azure.sql` (schema completo Azure SQL)
  - `services/identity/runtime-permissions.azure.sql` (grants mínimos de `SELECT, INSERT, UPDATE, DELETE` para a identidade de runtime nas novas tabelas, sem `ALTER/DROP/CONTROL`)
  - `services/identity/migrations/002_member_area_additive.azure.sql` (migração aditiva idempotente para Azure SQL)
  - `services/identity/migrations/002_member_area_rollback.azure.sql` (script de rollback controlado)
- **Status de execução**:
  - **Validado localmente** em SQLite em memória/disco durante toda a suíte de testes (`83` testes) e no servidor local de verificação.
  - **NÃO executado em nuvem** (`sql-anderzilla-ident-brs / sqldb-anderzilla-identity`), em cumprimento estrito à restrição operacional do prompt.

---

## 5. Matriz de Testes (`A01–A09`, `N01–N03`, `P01–P05`, `K01–K09`, `O01–O04`)

Todos os cenários definidos em `operations/MEMBER-AREA-DELIVERY.md` foram implementados e verificados:

| ID | Cenário | Teste Automatizado / Evidência | Resultado |
|---|---|---|---|
| `A01` | Visitante anônimo e `Origin` inválida bloqueados em todas as rotas `/api/member/*` e `/api/points/*` | `test_a01_anonymous_and_origin_protection` (`services/identity/test_member_area.py`) | **PASS** (`401 authentication_required` / `403 invalid_origin`) |
| `A02` | Conta autenticada com onboarding incompleto ou e-mail não verificado bloqueada em `/api/member/*` e `/api/points/*` | `test_a02_incomplete_and_unverified_blocked_from_member_and_points` | **PASS** (`403 onboarding_required` / `403 email_unverified`) |
| `A03` | Token inválido/expirado (`401`) e conta suspensa/banida (`403 account_unavailable`) rejeitados no servidor | `test_a03_suspended_account_and_invalid_token_rejected` | **PASS** |
| `A04` | Isolamento IDOR/BOLA entre Conta A e Conta B em mochila, radar, interesses e exploração | `test_a04_a05_idor_and_cross_account_isolation` | **PASS** |
| `A05` | Isolamento IDOR/BOLA em `challenges/{attemptId}`, `evidence`, `pending/claim` e `operations/{operationId}` | `test_a04_a05_idor_and_cross_account_isolation` | **PASS** (`404 not_found`) |
| `A06` | Logout imediato, incremento de `sessionEpoch`, aborto de `fetch` em voo, revogação de `ObjectURL`, invalidação multi-aba (`BroadcastChannel`) e aviso `logout_unconfirmed` | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` | **PASS** |
| `A07` | Auditoria do build estático (`apps/web/out`): `noindex, nofollow` em todas as rotas `/conta` e `/account`, ausência em `sitemap.xml`, `Disallow` em `robots.txt` e zero vazamento de dados privados/gabaritos | `test_a07_static_export_privacy_and_sitemap_audit` | **PASS** (`21` arquivos HTML auditados) |
| `A08` | Item salvo na mochila que vira `draft`, é removido ou exige `entitlement` não concedido retorna placeholder seguro (`available: false`) sem vazar metadados privados | `test_a08_unavailable_and_entitled_items_never_leak_metadata` | **PASS** |
| `A09` | Rejeição de campos de autoridade/privilégio enviados pelo cliente (`role`, `isAdmin`, `plan`, `entitlements`, `award`, `balance`, `cpf`, `birthDate`, `accountId`) | `test_a09_rejects_client_authority_and_privilege_fields` | **PASS** (`422 invalid_fields`) |
| `N01` | Visitante vê apenas `Entrar` no cabeçalho; clicar em salvar artigo registra intenção pós-login sanitizada e exige confirmação explícita após autenticar | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` + `ArticleMemberBar.tsx` | **PASS** |
| `N02` | Membro vê `Seu Radar`, chip `KP` e menu disclosure acessível (`aria-expanded`, `aria-controls`, `Escape` retorna foco ao botão, 10 itens canônicos) | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` + `AccountUI.tsx` | **PASS** |
| `N03` | Sanitização estrita de `returnTo` (`sanitizeInternalReturnPath`) bloqueando `https://evil.example`, `//evil`, `javascript:` e rotas fora da allowlist | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` | **PASS** |
| `P01` | Mochila: `PUT` e `DELETE` idempotentes e restauração via desfazer (`undo`) | `test_p01_backpack_idempotent_save_remove_and_undo` | **PASS** |
| `P02` | Interesses: `PUT /api/member/interests` com `expectedVersion`, conflito entre abas (`409 interests_conflict`) e suporte a `0` temas selecionados | `test_p02_interests_version_concurrency_and_empty_valid` | **PASS** |
| `P03` | Seu Radar: estado vazio orientativo quando `0` interesses e filtro temporário (`?category=`) sem alterar interesses persistidos | `test_p03_member_radar_empty_and_temporary_filter_does_not_mutate_interests` | **PASS** |
| `P04` | Exploração: deduplicação por descoberta, `0 KP` por leitura, limpeza atômica com incremento de `historyGeneration` e rejeição de evento atrasado (`409 stale_exploration_event`) | `test_p04_exploration_deduplication_clear_generation_and_zero_kp` | **PASS** |
| `P05` | Paginação determinística por cursor composto em coleção com `1.050` itens (`21` páginas de `50` itens) sem duplicatas ou omissões + `422 invalid_cursor` | `test_p05_backpack_pagination_over_1000_items` | **PASS** |
| `K01` | Fonte única de carteira KP (`/api/account/me`, `/api/member/dashboard`, `/api/points/wallet` e cabeçalho leem a mesma carteira do servidor; sem carteira paralela local) | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` + `test_k02_k03_k04...` | **PASS** |
| `K02` | Idempotência e concorrência no `POST /api/points/pending/claim`: chamadas paralelas geram exatamente `1` recibo e `1` crédito no ledger | `test_k02_k03_k04_single_wallet_claim_idempotency_conflict_and_status_recovery` | **PASS** |
| `K03` | Reuso da mesma `Idempotency-Key` com payload diferente retorna `409 idempotency_conflict` | `test_k02_k03_k04_single_wallet_claim_idempotency_conflict_and_status_recovery` | **PASS** |
| `K04` | Recuperação de status pré-`operationId` via `GET /api/points/operation-status?type=claim` usando `Idempotency-Key` | `test_k02_k03_k04_single_wallet_claim_idempotency_conflict_and_status_recovery` | **PASS** |
| `K05` | Expiração de `pendingClaim` (`410 claim_expired`), liberação única de orçamento reservado (`release_expired_claims`) e estados `new_activity_paused` (`409`) / `maintenance` (`503`) | `test_k05_expiry_reservation_release_and_program_states` | **PASS** |
| `K06` | Atomicidade transacional: falha injetada entre `mission_completions`, `point_ledger` e `wallets` faz rollback completo e mantém `reconcile_wallets` íntegro | `test_k06_transactional_atomicity_on_mid_claim_failure` | **PASS** |
| `K07` | Desacoplamento de superfície demo: atividades de demonstração não creditam KP e missões oficiais exigem sessão verificada | `test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts` + `test_identity.py` | **PASS** |
| `K08` | Backfill aditivo e idempotente de `preferences_bookmarks` para `member_interests`, `member_bookmarks` e `member_exploration` sem importar dados locais nem conceder KP | `test_k08_additive_backfill_from_preferences_bookmarks` | **PASS** |
| `K09` | Contenção de orçamento final de campanha entre duas contas (`budget_kp=25` disputado por `Player1` e `Player2`): exatamente uma aprova (`200`) e a outra recebe `409 reward_capacity` | `test_k09_campaign_budget_contention_between_accounts` | **PASS** |
| `O01` | Exportação LGPD (`GET /api/account/export`) inclui perfil, interesses, mochila, exploração, missões e extrato KP | `test_o01_o04_export_delete_releases_reservation_and_production_gate` | **PASS** |
| `O02` | Exclusão de conta (`POST /api/account/delete`) exige step-up reauth recente (`<= 300s`, senão `403 reauth_required`), limpa dados pessoais/coleções e libera reservas KP pendentes | `test_o01_o04_export_delete_releases_reservation_and_production_gate` | **PASS** |
| `O03` | Ferramentas de operador (`reconcile-wallets`, `release-expired-claims`, `backfill-collections`) em `services/identity/managed_operator.py` | `test_k02_k03_k04...`, `test_k05...`, `test_k08...` | **PASS** |
| `O04` | Gate operacional de produção: sem `IDENTITY_REWARDS_ENABLED=true` e `IDENTITY_KP_PROGRAM_STATE=active`, o programa permanece `disabled` por padrão | `test_o01_o04_export_delete_releases_reservation_and_production_gate` | **PASS** |

---

## 6. Resultados de Build, Testes, Acessibilidade e Responsividade

1. **Build estático Next.js (`apps/web`)**:
   - Comando: `npm --prefix apps/web run build`
   - Resultado: **Exit code 0** (`227/227` páginas estáticas geradas com sucesso em `apps/web/out`, incluindo `/pt/conta/*`, `/en/conta/*`, `/pt/conta/missoes/[id]`, `/en/conta/missoes/[id]` e `/account`).
2. **Suíte de testes automatizados Python (`services/identity`)**:
   - Comando: `python -m unittest discover -s services/identity -t .`
   - Resultado: **Ran 83 tests in 11.587s — OK** (`test_identity.py`, `test_clerk.py`, `test_function_app.py` e `test_member_area.py`).
3. **Verificação E2E HTTP em loopback (`scripts/member_area_local_server.py`)**:
   - Servidor local iniciado em `http://127.0.0.1:4173` servindo `apps/web/out` + `/api/*`.
   - Todas as rotas HTML estáticas (`/pt/conta/*`, `/en/conta/*`, `/account/`), guardas `401`/`403`, Painel do Jogador, Interesses, Mochila, Exploração e fluxo completo de Missão + Claim KP (`checkpoint-curiosidade` -> `+25 KP`) responderam conforme especificado.
4. **Acessibilidade e Responsividade**:
   - Skip links presentes (`#member-main`, `#hub-main`, `#article`).
   - Menu do cabeçalho implementado como disclosure navigation (`<button aria-expanded={menuOpen} aria-controls="member-navigation-disclosure">` + `<nav id="member-navigation-disclosure">`), fechando com `Escape` e devolvendo foco ao botão gatilho.
   - Alvos de toque mínimos de `44x44px` (`min-height: 44px`), foco visível `:focus-visible`, suporte a `@media (prefers-reduced-motion: reduce)` e grids responsivos em `account.css` para `360px`, `768px`, `1024px` e `1440px` sem overflow horizontal.

---

## 7. Riscos Residuais e Dependências Operacionais Externas

1. **Execução da migração SQL em nuvem (`002_member_area_additive.azure.sql`)**:
   - Quando a revisão independente do Codex autorizar a promoção para homologação/produção, o operador deverá aplicar `services/identity/migrations/002_member_area_additive.azure.sql` e `services/identity/runtime-permissions.azure.sql` no banco `sqldb-anderzilla-identity` (`sql-anderzilla-ident-brs`) usando `services/identity/managed_operator.py` sob identidade Entra ID administrativa.
2. **Backfill inicial das contas existentes em nuvem**:
   - O `MemberAreaService` já realiza backfill aditivo automático por conta no primeiro acesso autenticado, e o comando `python services/identity/managed_operator.py backfill-collections` está pronto para execução em lote pelo operador após a migração SQL.
3. **Ativação futura de Karaca Points reais**:
   - Permanece condicionada à aprovação explícita do proprietário, campanha com cobertura orçamentária cadastrada em `mission_campaigns` e configuração explícita de `IDENTITY_REWARDS_ENABLED=true` e `IDENTITY_KP_PROGRAM_STATE=active`.

---

## 8. Confirmação Explícita de Segurança Operacional e Gate de Produção

- **Nenhuma publicação em produção ou homologação foi realizada** (nenhum deploy para Azure Static Web Apps ou Azure Functions foi disparado).
- **Nenhum merge foi feito em `develop` ou `main`** (todo o trabalho permanece isolado na branch `codex/member-area-antigravity`).
- **Nenhuma migração SQL, alteração de segredo, DNS ou permissão foi executada na nuvem**.
- **Karaca Points reais permanecem desabilitados por padrão em produção** (`IDENTITY_REWARDS_ENABLED=false` e `IDENTITY_KP_PROGRAM_STATE=disabled` em `infra/azure/identity-deploy.ps1` e `MemberAreaService`).
