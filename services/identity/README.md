# services/identity — AnderZilla Contas & Karaca Points (piloto)

Domínio exclusivo de contas públicas. Operado pelo coordenador via Azure Functions gerenciado SWA (Python 3.11) + Azure SQL (free, auto-pause). SQLite apenas para testes locais. Nenhum saldo demo migra como direito.

## Arquivos
- `CONTRACT.md` — contratos `/api/account/*` e `/api/points/*` (ler primeiro para frontend).
- `core.py` — domínio: register/verify/login/sessions/profile/export/delete, ledger append-only, missions idempotentes, pending_reward curto.
- `security.py` — hashing argon2→bcrypt, tokens hash SHA-256, cookies HttpOnly Secure SameSite, Origin/CSRF, rate persistente, OIDC Google real (iss/aud/nonce/PKCE).
- `email.py` — SMTP TLS adapter; sem SMTP → `503 email_unavailable`; capturer injetável só em testes.
- `storage.py` — `SQLiteStore` (local) e `AzureSQLStore` (SERIALIZABLE + sp_getapplock, certifi TLS).
- `api.py` — `dispatch(service, method, path, headers, body)` usado pelo Function App.
- `config.py` — fail-closed em `IDENTITY_ENV=production`.
- `schema.sql` / `schema.azure.sql` — DDL próprio (não reuse CMS).
- `DEPLOYMENT.md` — env keys sem values.
- `function_app.py` — template de integração SWA (coordenador implanta).

## Testes
```
python -m pytest services/identity -v
python -m unittest discover -s services/identity -v
```

## Notas de segurança
- `Principal` nunca vem do body; só de sessão validada.
- Email token hash single-use expiração; nunca retorna token em resposta.
- Sessão hash no banco; cookie `__Host-` Lax Secure HttpOnly 30d.
- Google só ativo com `IDENTITY_GOOGLE_*` completos; verificação real de JWK/issuer/aud/exp/nonce/PKCE.
- Ledger `TRIGGER` append-only; `requests` idempotência com payload hash.
- `pending_reward` 30 min ligado ao browser; claim revalida evidência — token não autoriza sozinho.
- Anonymous nunca recebe crédito; `email_verified` obrigatório para KP.
- Rate limits persistentes por scope/bucket.
