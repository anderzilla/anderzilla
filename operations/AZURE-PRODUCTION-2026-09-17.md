# Produção publicada — 17/09/2026

Publicado por volta de 2026-09-17T14:15Z (verificado às 14:28Z) em https://anderzilla.com e https://www.anderzilla.com (recurso `anderzilla-web-production`, grupo `anderzilla-web`, SKU Free). Mesma conta/tenant/assinatura conferidos pelo script (`anderzilla@ymail.com`, tenant `3fdcb773-0842-4fb9-925e-bea17d681f83`, assinatura `44b76346-26bd-4cd3-a529-627e47e99e5a`).

- Código-base: commit `00bdaf93d59dc1d78b4549f05f6bb8ecaa48bb8d` — o mesmo artefato já publicado em homolog nesta data (Trust & Commerce, backend/UI de contas, avatar de usuário, correções de gamificação/UX do login, revisão de textos legais LGPD/CDC/Marco Civil/Constituição). 163 arquivos, `npm run build` sem erros.
- **Pendência conhecida ao publicar:** homolog não recebeu revisão visual humana antes desta promoção (sem acesso `anderzilla_reviewer` disponível nesta sessão). Decisão do proprietário foi seguir direto para produção; verificação ficou por conta da inspeção pós-publicação abaixo, que é pública e não substitui uma revisão anterior por um revisor autenticado.

## Verificação pós-publicação

- HTTP 200 em `anderzilla.com`, `www.anderzilla.com` e no hostname Azure `mango-coast-0322c590f.5.azurestaticapps.net`.
- `robots.txt` permite indexação (`Allow: /`) e aponta `sitemap.xml`; nenhum header de `noindex`/`no-store` vazou da configuração de homolog.
- Rotas novas conferidas com 200: `/pt/comercio/brasil`, `/pt/comercio/internacional`, `/en/comercio/brasil`, `/pt/privacidade`, `/pt/termos`, `/pt/cookies`. Redirecionamentos legados (`/forgekit`, `/stackpick`) preservados (301). Caminho inexistente retorna 404.
- Inspeção visual real no navegador: home renderiza sem erro de console; hub Área Brasil mostra o estado vazio honesto ("Ainda sem ofertas ativas nesta área", sem inventar oferta); página de Privacidade mostra o texto legal revisado (base legal, LGPD/CDC/Marco Civil/Constituição) publicado corretamente; diálogo de login mostra "Contas ainda indisponíveis neste ambiente" — esperado, pois `NEXT_PUBLIC_ACCOUNT_API_BASE` não está configurado em produção e `services/identity` não foi implantado no Azure. Nenhum crédito de KP, saldo ou conta funcional foi exposto.
- Sitemap inclui as URLs esperadas com `lastmod` do build atual.

## O que continua não implantado

`services/identity` (contas/Karaca Points reais) segue sem infraestrutura Azure própria — os scripts `infra/azure/identity-*.ps1` existem mas não foram executados. Em produção isso aparece como "indisponível", nunca como erro ou dado inventado, por desenho. Publicar esse backend é uma decisão e execução separadas desta.

## Rollback

Reconstruir a revisão anterior (branch `codex/anderzilla-foundation`, commit anterior a `00bdaf9` com build de `apps/web`) e republicar com o mesmo `infra/azure/deploy.ps1 -Environment production`. Nenhuma migração de dados está envolvida (export estático); rollback é apenas trocar o artefato publicado.
