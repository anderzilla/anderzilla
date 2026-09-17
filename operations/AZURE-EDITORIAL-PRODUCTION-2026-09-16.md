# Publicação editorial em produção — 16/09/2026

Confirmada em 2026-09-17T02:17:20.731928+00:00 em https://anderzilla.com e https://www.anderzilla.com.

- Azure Static Web Apps Free: anderzilla-web-production; identidade, assinatura e tenant conferidos pelo script de deploy. DNS e email preservados.
- Snapshot CMS `40565a1a-f845-4294-b216-1cff2540065a`, SHA256 `c424f7ab817c2e5d9452878e9e59d01b4ebf6869051dfdcc94467c9982f1eb73`. 60 matérias PT/EN, 50 capas das fontes, 35 galerias e 10 alternativas editoriais.
- Build de 138 páginas aprovado; 120 páginas de artigos conferidas byte a byte contra o artefato publicado; 242 URLs de imagens/previews responderam HTTP 200.
- Robots permite indexação, sitemap inclui as 120 URLs editoriais, HTTPS válido nos dois domínios e rota inexistente retorna 404.
- Inspeção no navegador confirmou fotos, créditos, metadados sociais e cabeçalho sem o antigo rótulo de prévia. Avisos de pontos demonstrativos preservados.
- Código base `645b07d7275e9e0fce3470abd94f51bbf8c153ba` mais alterações locais preservadas em `production-working-tree.patch` (SHA256 `6ed8daeaacaaa46a71827b8b995603257893dbdb4835b27d872d7355181cce44`), no diretório editorial real-media-2026-09-16.
- Artefato imutável: `Z:\AnderZilla\.deploy\production-40565a1a-f845-4294-b216-1cff2540065a-launch`. Manifesto: `production-artifact-sha256.json` no mesmo diretório editorial.

## Rollback

Versão pública anterior salva em `Z:/AnderZilla/.deploy/production-before-real-media-20260916`: 70 arquivos conferidos contra AZURE-ARTIFACT.json antes da publicação.

Para restaurar, executar `infra/azure/deploy.ps1 -Environment production -ArtifactPath 'Z:/AnderZilla/.deploy/production-before-real-media-20260916' -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'`, com AZURE_CONFIG_DIR=C:/Users/ander/.codex/anderzilla-azure. Conferir HTTPS e páginas após o deploy. Não alterar DNS.

As revisões das matérias e mídias permanecem no CMS. A promoção reutiliza o snapshot aprovado; não cria notícias duplicadas nem muda o estado da prévia visual.
