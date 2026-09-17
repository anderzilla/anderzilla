# BRIEF 1 — Segurança, termos e burocracia (checklist + páginas)

## Entregar

1. Páginas `/[lang]/privacidade`, `/[lang]/termos`, `/[lang]/cookies` (ou estender privacy/terms existentes) PT+EN.
2. Banner/preferências de cookies (essenciais vs analytics se houver — hoje sem inventar trackers).
3. Fluxos: idade mínima (13+/18+ conforme decisão documentada), consentimento marketing separado, exclusão de conta, exportação de dados (LGPD art. 18 — checklist).
4. Política Karaca Points: não dinheiro, não venda, demo vs produção, contestação.
5. Security baseline: HTTPS only, cookies httpOnly/secure/SameSite, CSRF em mutações, rate limit login/register/verify, hashing senha (argon2/bcrypt), sem secrets no front, logs sem PII excessiva.
6. Documento `docs/AUTH-LEGAL-SECURITY-CHECKLIST.md` marcando o que é **texto provisório** vs **precisa advogado BR**.

Não afirmar conformidade jurídica total — implementar controles técnicos e copy honesta.