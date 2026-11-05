# Deploy do site (apps/web → Azure Static Web Apps)

## Fluxo
```
feature/ops branch → PR → codex/anderzilla-foundation
foundation → develop (push)  → homolog automático (privado, revisores convidados)
develop → main (fast-forward) → produção, após aprovação no environment `production`
```

- A produção publica **o mesmo artefato** homologado para aquele commit; não há rebuild.
- `main` deve receber `develop` por **fast-forward** (`git push origin develop:main`), nunca squash/merge commit — o workflow procura o run de homolog com o mesmo SHA.
- Rollback: Actions → "Azure web release" → Run workflow na `main`, informando o ID de um run de homolog anterior bem-sucedido.

## Pré-requisitos (configurados pelo proprietário no GitHub)
| Item | Onde |
|---|---|
| Environment `homolog` + secret `AZURE_STATIC_WEB_APPS_API_TOKEN` (token da SWA `anderzilla-web-homolog`) | Settings → Environments |
| Environment `production` + secret `AZURE_STATIC_WEB_APPS_API_TOKEN` (token da SWA `anderzilla-web-production`) | Settings → Environments |
| `production`: Required reviewers = proprietário; Deployment branches = somente `main` | Settings → Environments → production |
| Branches `develop` e `main` | criadas a partir de `codex/anderzilla-foundation` |

Tokens nunca entram em código, chat ou logs. Para rotacionar: Azure portal → Static Web App → Manage deployment token → atualizar o secret.

## Deploy manual (fallback)
`./infra/azure/deploy.ps1 -Environment homolog|production -AzureCli <caminho do az>` no PowerShell do proprietário (ver operations/AZURE-RELEASE.md na branch de docs).
