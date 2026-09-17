# AnderZilla Identity & Karaca Points — API Contract (services/identity)

**Base prefix:** `/api/account/*` (conta) e `/api/points/*` (KP). Versionamento futuro em `/api/v1`; prefixo curto mantido por simplicidade do piloto SWA. Todas respostas privadas `Cache-Control: no-store`. Erros estruturados `{error:{code,message,correlationId}}`. Nunca retorna stack/SQL. `401` sem sessão, `403` conta suspensa/inativa, `404` recurso alheio, `409` idempotência/version, `422` payload, `429` rate limit, `503` indisponível/verificador desabilitado/banco pausado.

**Sessão:** cookie `__Host-anderzilla_sid` HttpOnly Secure SameSite=Lax Path=/ Max-Age 30d. Valor = token aleatório 32 bytes hex; armazenamento é hash SHA-256. Toda mutação exige `Origin` == `IDENTITY_ALLOWED_ORIGIN` e `Content-Type: application/json`. Sem Origin em produção → `403`. Sem header `x-ms-client-principal` nunca confia.

**Rate limit persistente:** tabela `rate_limits` por chave `(scope,bucket)` janela deslizante server-side (login/register/verify/google). Excede → `429` com `Retry-After`.

**Email verification:** `POST /api/account/register` cria conta `email_verified=0` + token aleatório, hash SHA-256 single-use expiração `IDENTITY_VERIFY_TTL_HOURS` (default 24h). Email enviado via SMTP TLS se `IDENTITY_SMTP_HOST` configurado; sem SMTP → `503 email_unavailable` (nunca loga token nem retorna em corpo). `POST /api/account/verify` recebe `{token}` cru, compara hash, marca `email_verified=1`. Reuso/expirado → `410`/`422`.

**Google OIDC:** só ativo se `IDENTITY_GOOGLE_CLIENT_ID` + `IDENTITY_GOOGLE_CLIENT_SECRET` + `IDENTITY_GOOGLE_REDIRECT_URI` presentes. Em produção sem essas env → fail-closed `503 google_unavailable`. Verificação real: `iss` = `https://accounts.google.com` ou `accounts.google.com`, `aud` == client_id, `exp`>now, `nonce` confere com `oauth_nonces` (PKCE `code_verifier`/`code_challenge` S256 quando fluxo code), `state` one-time. Nunca cria conta automaticamente sem `email_verified` do Google = true.

**KP regras:** `POST /api/points/claim` só com `email_verified=1` + `state=active`. `awardKP` definido server-side em `missions(id,version)`. Evidência `evidence_ref` validada contra tabela `mission_evidence` (quiz attempt / interests snapshot) ownership. `Idempotency-Key: 8–128 chars` obrigatório; hash canônico do payload vinculado; replay igual → mesmo `completionId`, payload diferente → `409`. `pending_reward` token curto (30 min) ligado ao browser (`browser_token_hash`) — `POST /api/points/pending` cria preview anônimo, `POST /api/points/pending/claim` após login revalida evidência e só então credita ledger. Token jamais autoriza crédito sem revalidação.

**Perfil & sync:** `PATCH /api/account/profile` campos `displayName, lang(pt-BR|en), interests[≤6], timezone, marketingOptIn, saved[], opened[]`. `saved/opened` são `contentId` opacos já publicados; não importa saldo demo. `GET /api/account/export` dump LGPD, `POST /api/account/delete` soft-delete + revoke sessions, ledger preservado append-only com `account_id` anonimizado.

## Endpoints

| Método | Rota | Auth | Body / Query | Sucesso |
|---|---|---|---|---|
| POST | /api/account/register | não | `{email,password,displayName,lang?,timezone?,marketingOptIn?,interests?}` | 201 `{accountId, message:"verify_email_sent"}` (nunca token) |
| POST | /api/account/verify | não | `{token}` | 200 `{verified:true}` |
| POST | /api/account/login | não | `{email,password}` | 200 `{accountId}` + Set-Cookie |
| POST | /api/account/logout | cookie | — | 204 clear cookie |
| POST | /api/account/logout-all | cookie | — | 204 |
| GET | /api/account/me | cookie | — | 200 `{account:{id,email,emailVerified,displayName,lang,timezone,marketingOptIn,interests,saved,opened}, wallet:{available,reserved}}` |
| PATCH | /api/account/profile | cookie | `{displayName?,lang?,timezone?,marketingOptIn?,interests?,saved?,opened?}` | 200 profile |
| GET | /api/account/export | cookie | — | 200 JSON export |
| POST | /api/account/delete | cookie | `{confirm:"DELETE"}` | 204 |
| POST | /api/account/oauth/google/start | não | `{}` | 200 `{url,state,nonce}` se configurado senão 503; state/nonce PKCE salvos httpOnly |
| POST | /api/account/oauth/google/callback | não | `{code,state}` ou `{idToken,nonce}` | 200 `{accountId}` + cookie; verifica iss/aud/exp/nonce/PKCE real |
| GET | /api/points/wallet | cookie | — | 200 `{available,reserved,unit:"KP"}` |
| GET | /api/points/ledger | cookie | `?cursor&limit(1-100)` | 200 `{items,nextCursor}` newest first |
| GET | /api/points/missions | cookie/opt | — | 200 `{items:[{id,version,awardKP,startsAt,endsAt}]}` |
| POST | /api/points/claim | cookie | `{missionId,missionVersion,evidenceRef}` + `Idempotency-Key` | 200 `{completionId}` |
| POST | /api/points/pending | não | `{missionId,missionVersion,evidenceRef}` | 200 `{pendingToken, expiresAt}` (token browser-only, curto, não autoriza crédito) |
| POST | /api/points/pending/claim | cookie | `{pendingToken}` + `Idempotency-Key` | 200 `{completionId}` após revalidar evidência |
| GET | /api/points/rewards | cookie | — | 200 `{items}` (catálogo futuro; sem resgate real nesta fase) |

**Notas frontend:** exibir popup “crie conta para salvar X KP” quando `pendingToken` recebido sem sessão; nunca mostrar saldo derivado de localStorage. Respeitar `503` com banner “serviço indisponível” sem fallback local.
