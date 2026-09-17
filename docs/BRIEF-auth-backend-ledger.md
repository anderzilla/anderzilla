# BRIEF 2 — Backend: auth, e-mail, OAuth, ledger Karaca

Preferir estender `services/cms` / novo `services/identity` ou `services/rewards` já previsto — Azure como fonte de verdade; sem misturar admin Entra.

## Conta

- Email+senha com verificação (magic link ou código OTP por e-mail).
- Campos perfil: display name, idioma, interesses, timezone America/Sao_Paulo default, marketing opt-in.
- Atualização de dados + delete account + session revoke.
- OAuth Google (OIDC). Instagram: pesquisar viabilidade 2026; se Login Instagram app não servir third-party web, usar Meta Login ou adiar com nota no gap doc — **não fake button**.

## Ledger KP

- Tabelas: users, email_verifications, oauth_identities, sessions, wallets, ledger_entries, missions, mission_claims (idempotent).
- Creditar KP só após: user verified + mission rules server-side + anti-replay.
- Popup claim: pending_reward token de curta duração ligado ao browser→liga à conta no signup.
- XP separado de KP se seguir KARACA-ECONOMY (pode ser fase 2).

## APIs

Auth register/login/logout/verify/me/profile; rewards balance/history/claim; admin flags CMS para missões.

Testes automatizados de idempotência e “sem conta = sem crédito”.