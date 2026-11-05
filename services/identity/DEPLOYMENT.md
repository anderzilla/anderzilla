# Identity — Required Environment Keys (no values)

> Estas chaves descrevem o modo nativo legado. A fase 1 com Clerk está documentada em [CLERK.md](CLERK.md), incluindo bearer, cadastro privado, webhook e variáveis de build. Não implantar o serviço legado sobre produção para habilitar Clerk.

> Nunca commitar valores. Em `IDENTITY_ENV=production` faltas causam fail-closed (503).

## Core
- `IDENTITY_ENV` = `homolog` | `production`
- `IDENTITY_ALLOWED_ORIGIN` = `https://anderzilla.com` (ou homolog origin)
- `IDENTITY_VERIFY_URL_BASE` = `https://anderzilla.com/verify` (base para link de verificação)
- `IDENTITY_VERIFY_TTL_HOURS` = `24` (default)
- `IDENTITY_SESSION_TTL_DAYS` = `30`
- `IDENTITY_PENDING_TTL_MINUTES` = `30`
- `IDENTITY_RATE_WINDOW_SECONDS` = `900`
- `IDENTITY_RATE_MAX_ATTEMPTS` = `5`

## Azure SQL (obrigatório em produção)
- `IDENTITY_SQL_SERVER`
- `IDENTITY_SQL_DATABASE`
- `IDENTITY_SQL_USER`
- `IDENTITY_SQL_PASSWORD`

## Email (SMTP TLS) — sem isto `/register` e `/verify` retornam 503 email_unavailable
- `IDENTITY_SMTP_HOST`
- `IDENTITY_SMTP_PORT` (default 587)
- `IDENTITY_SMTP_USER`
- `IDENTITY_SMTP_PASSWORD`
- `IDENTITY_SMTP_FROM` (obrigatório se HOST setado)
- `IDENTITY_SMTP_TLS` = `true`|`false` (default true)

## Google OIDC — só ativo se os três presentes; incompleto → 503 google_unavailable
- `IDENTITY_GOOGLE_CLIENT_ID`
- `IDENTITY_GOOGLE_CLIENT_SECRET`
- `IDENTITY_GOOGLE_REDIRECT_URI` (ex: `https://anderzilla.com/api/account/oauth/google/callback`)

## Observações
- Não usar `IDENTITY_SQL_*` iguais ao CMS; criar usuário contido dedicado `anderzilla_identity_runtime`.
- Ver `runtime-permissions.azure.sql` para GRANTs mínimos.
- Em homolog sem SMTP/Google o serviço sobe mas rotas retornam `503` honesto.
