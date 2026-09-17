# AnderZilla Identity & Karaca Points — API Contract (services/identity)

**Base prefix:** `/api/account/*` (conta) e `/api/points/*` (KP). Versionamento futuro em `/api/v1`; prefixo curto mantido por simplicidade do piloto SWA. Todas respostas privadas `Cache-Control: no-store`. Erros estruturados `{error:{code,message,correlationId}}`. Nunca retorna stack/SQL. `401` sem sessão, `403` conta suspensa/inativa, `404` recurso alheio, `409` idempotência/version, `422` payload, `429` rate limit, `503` indisponível/verificador desabilitado/banco pausado.

**Sessão:** cookie `__Host-anderzilla_sid` HttpOnly Secure SameSite=Lax Path=/ Max-Age 30d. Valor = token aleatório 32 bytes hex; armazenamento é hash SHA-256. Toda mutação exige `Origin` == `IDENTITY_ALLOWED_ORIGIN` e `Content-Type: application/json`. Sem Origin em produção → `403`. Sem header `x-ms-client-principal` nunca confia.

**Contexto/CSRF:** cookie separado `__Host-anderzilla_context` (valor `browserToken.csrfToken`, 43 chars cada, gerado em `GET /api/account/capabilities` na primeira visita) identifica o navegador e carrega o token CSRF. Toda mutação exige o mesmo `csrfToken` no header `X-CSRF-Token`; sem contexto ou token divergente → `403 csrf_failed`. O `csrfToken` também é devolvido no corpo de `/api/account/capabilities` e de `/api/account/me`, para o cliente atualizar sua cópia.

**Rate limit persistente:** tabela `rate_limits` por chave `(scope,bucket)` janela deslizante server-side (login/register/verify/google). Excede → `429` com `Retry-After`.

**Email verification:** `POST /api/account/register` cria conta `email_verified=0` + token aleatório, hash SHA-256 single-use expiração `IDENTITY_VERIFY_TTL_HOURS` (default 24h). Email enviado via SMTP TLS se `IDENTITY_SMTP_HOST` configurado; sem SMTP → `503 email_unavailable` (nunca loga token nem retorna em corpo). `POST /api/account/verify` recebe `{token}` cru, compara hash, marca `email_verified=1`. Reuso/expirado → `410`/`422`.

**Google OIDC:** só ativo se `IDENTITY_GOOGLE_CLIENT_ID` + `IDENTITY_GOOGLE_CLIENT_SECRET` + `IDENTITY_GOOGLE_REDIRECT_URI` presentes. Em produção sem essas env → fail-closed `503 google_unavailable`. Verificação real: `iss` = `https://accounts.google.com` ou `accounts.google.com`, `aud` == client_id, `exp`>now, `nonce` confere com `oauth_nonces` (PKCE `code_verifier`/`code_challenge` S256 quando fluxo code), `state` one-time. Nunca cria conta automaticamente sem `email_verified` do Google = true.

**KP regras:** fluxo real é `missões → desafio → evidência → prévia/crédito`, não um único `pending` anônimo. `GET /api/points/missions` lista missões ativas com `titlePT`/`titleEN` obrigatórios (extraídos de `definition_json`; missão com definição inválida some da lista em vez de quebrá-la). `POST /api/points/challenge {missionId,missionVersion}` cria uma tentativa (`challenges`, expira em 30 min) e devolve `titlePT/titleEN` + perguntas (quiz) sem a resposta correta. `POST /api/points/evidence {challengeId,answers?,interests?}` valida a resposta contra o `definition_hash` da tentativa e devolve `pendingToken` curto ligado ao navegador (`browser_hash`), não autenticado. `POST /api/points/claim {missionId,missionVersion,evidenceRef}` (sessão já existente) ou `POST /api/points/pending/claim {pendingToken}` (visitante que acabou de logar) exigem `email_verified=1` + `state=active` + `Idempotency-Key: 8–128 chars`; hash canônico do payload vinculado, replay igual → mesmo `completionId`, payload diferente → `409`. `IDENTITY_KP_CYCLE_BUDGET` limita o total creditado por ciclo (esgotado → `reward_capacity`, sem crédito parcial). Token de prévia jamais autoriza crédito sem essa revalidação.

**Perfil & sync:** `PATCH /api/account/profile` campos `displayName, lang(pt-BR|en), interests[≤6], timezone, marketingOptIn, saved[], opened[]`. `saved/opened` são `contentId` opacos já publicados; não importa saldo demo. `GET /api/account/export` dump LGPD, `POST /api/account/delete` soft-delete + revoke sessions, ledger preservado append-only com `account_id` anonimizado.

## Endpoints

| Método | Rota | Auth | Body / Query | Sucesso |
|---|---|---|---|---|
| GET | /api/account/capabilities | não | — | 200 `{available,registration,emailPassword,google,meta,passwordReset,emailResend,rewards,minimumAge,termsVersion,privacyVersion,csrfToken}`; emite cookie de contexto na primeira chamada |
| POST | /api/account/register | contexto+CSRF | `{email,password,displayName,lang?,timezone?,marketingOptIn?,interests?,ageConfirmed,termsAccepted,termsVersion,privacyVersion}` | 201 conta criada `email_verified=0`, e-mail de verificação enviado (nunca retorna token) |
| POST | /api/account/verify | contexto+CSRF | `{token}` | 200 `{verified:true}` |
| POST | /api/account/resend | contexto+CSRF, sessão de conta não verificada | — | 200 reenvia e-mail de verificação |
| POST | /api/account/login | contexto+CSRF | `{email,password}` | 200 `{accountId}` + Set-Cookie de sessão |
| POST | /api/account/logout | contexto+CSRF | — | 200, revoga sessão |
| GET | /api/account/me | cookie de sessão | — | 200 `{account:{id,email,emailVerified,displayName,lang,timezone,marketingOptIn,interests,saved,opened,hasPassword}, csrfToken}` |
| PATCH | /api/account/profile | cookie+CSRF | `{displayName?,lang?,timezone?,marketingOptIn?,interests?,saved?,opened?}` | 200 `{account}` |
| GET | /api/account/export | cookie de sessão | — | 200 JSON export (LGPD, art. 18) |
| POST | /api/account/delete | cookie+CSRF | `{confirm:"DELETE",password?}` | 200/204, revoga sessões |
| POST | /api/account/oauth/google/start | contexto+CSRF | `{ageConfirmed,termsAccepted,termsVersion,privacyVersion,lang?,marketingOptIn?}` | 200 `{url}` (state/nonce/PKCE salvos server-side) se `google` habilitado, senão 503 |
| POST | /api/account/oauth/google/callback | contexto+CSRF | `{code,state}` | 200 `{accountId}` + cookie; verifica iss/aud/exp/nonce/PKCE real; `account_link_required` se o e-mail já usa senha |
| GET | /api/points/wallet | cookie, e-mail verificado | — | 200 `{available,reserved}` |
| GET | /api/points/ledger | cookie, e-mail verificado | `?cursor&limit(1-100)` | 200 `{items,nextCursor}` newest first |
| GET | /api/points/missions | opcional | — | 200 `{items:[{id,version,awardKP,kind,startsAt,endsAt,titlePT,titleEN}]}`; `[]` se `rewards` desligado |
| POST | /api/points/challenge | contexto+CSRF | `{missionId,missionVersion}` | 200 `{challengeId,kind,expiresAt,titlePT,titleEN,questions?}` |
| POST | /api/points/evidence | contexto+CSRF | `{challengeId,answers?,interests?}` | 200 `{pendingToken,evidenceRef,missionId,missionVersion,awardPreview,expiresAt}` — prévia, não é saldo |
| POST | /api/points/claim | cookie+CSRF, e-mail verificado | `{missionId,missionVersion,evidenceRef}` + `Idempotency-Key` | 200 `{completionId}` |
| POST | /api/points/pending/claim | cookie+CSRF, e-mail verificado | `{pendingToken}` + `Idempotency-Key` | 200 `{completionId}` após revalidar evidência |
| GET | /api/points/rewards | cookie de sessão | — | 200 `{items:[],nextCursor:null}` (catálogo futuro; sem resgate real nesta fase) |

**Notas frontend:** mostrar convite para criar conta/entrar quando uma `evidence` gera `pendingToken` sem sessão verificada; nunca mostrar saldo derivado de localStorage. Respeitar `503`/`rewards_unavailable` com aviso claro, sem fallback local para saldo oficial.
