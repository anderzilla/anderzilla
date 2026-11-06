# Área do jogador — produção em 06/11/2026

## Atualização de navegação e sessão

- Frontend `94a7d72` publicado no portal de produção a partir de `.deploy/production-member-session-20261106`, com manifestos do build e das somas SHA256. API e banco permaneceram na versão anterior. Rollback do frontend: `.deploy/production-member-area-20261105`.
- A sessão Clerk fica no provedor do layout raiz. Links e trocas de seção/idioma usam o roteador do cliente, sem remontar o provedor. Clerk gerencia tokens e expiração; o navegador guarda somente um indicador de retomada, sem armazenar JWT por conta própria.
- Consultas simultâneas ao perfil são agrupadas por geração de sessão. Ao voltar à aba, a atualização ocorre em segundo plano se a última consulta bem-sucedida tiver pelo menos um minuto. A limpeza em saída/troca de identidade permanece; API mantém autorização server-side.
- Login, cadastro, gerenciamento de credenciais e missões são montados sob demanda. Telas de coleção não refazem consultas apenas porque o objeto de perfil foi atualizado.
- Build aprovado. Navegador local com conta sintética: painel → mochila → interesses → voltar, sem tela de verificação entre rotas. Em produção, páginas do painel PT/EN, mochila e interesses retornaram HTTP 200 e corresponderam byte a byte ao artefato publicado. Não houve teste novo de login com conta real.

Publicado após autorização do proprietário. Código: `2dcd9237ab3faf75d0074593e8e765ceeacae83d`, branch `codex/member-area-antigravity`. O commit original `428816f` tinha bloqueios corrigidos; evidências em `docs/MEMBER-AREA-VALIDATION.md` na branch de código. Sem merge em main: os históricos não têm ancestral comum. Publicação pelos artefatos do commit indicado.

- Migração Azure SQL 002 aplicada em produção após retomada do banco, com conferência do schema. Dados existentes preservados; administrador temporário removido.
- API dedicada `anderzilla-identity-api`: pacote `identity-func-member-area-20261105.zip`, SHA256 `6e5978f8bdaeaf54ed876d2d1fdffbe4bedfca3c5bb095b4374215057fa84155`. Settings e pacote anteriores preservados para rollback privado.
- Portal `anderzilla-web-production`: artefato `.deploy/production-member-area-20261105` e manifestos correspondentes. Publicado no domínio `https://anderzilla.com`. Todas as URLs do sitemap anterior preservadas. Mídias verificadas no artefato de publicação.
- Verificações posteriores: home PT/EN, painel PT/EN, perfil, termos e privacidade HTTP 200; páginas de conta com noindex; dashboard e carteira negaram acesso anônimo e bearer inválido (401); preflight PUT de interesses (204) com origem exata; capabilities confirma `memberArea=true` e `rewards=false`.
- KP reais continuam desligados. Smoke em produção não incluiu login com conta real; fluxos autenticados foram exercitados com fixtures no navegador local e no banco SQL de homologação. Não declarar verificação autenticada de produção concluída.
- Rollback: restaurar artefato estático anterior e settings/pacote anterior da API, preservando schema aditivo e dados. Não executar rollback destrutivo das tabelas.
