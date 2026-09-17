# Homolog republicado — 17/09/2026

Publicado às 2026-09-17T14:12Z em https://salmon-stone-0a4d29c0f.5.azurestaticapps.net (recurso `anderzilla-web-homolog`, grupo `anderzilla-web`, SKU Free). Conta/tenant/assinatura conferidos pelo script antes do deploy (`anderzilla@ymail.com`, tenant `3fdcb773-0842-4fb9-925e-bea17d681f83`, assinatura `44b76346-26bd-4cd3-a529-627e47e99e5a`).

- Código-base: commit `d3cf0064709ae59c2ec55fac4b222f62734ed5f1` (branch `codex/anderzilla-foundation`) — inclui Trust & Commerce, backend/UI de contas (`services/identity`), avatar de usuário, correções de gamificação/UX do fluxo de login e a revisão de textos legais (LGPD/CDC/Marco Civil/Constituição) feitas nesta sessão.
- `npm run build` em `apps/web`: 163 arquivos exportados, sem erros.
- Verificação HTTP pós-deploy: requisição anônima retornou `401` (`Cache-Control: no-store`), confirmando que a role `anderzilla_reviewer` continua exigida — nenhum conteúdo ficou público nesta publicação.
- Este recurso homolog é o app "produção" interno do slot homolog (terminologia da SWA CLI); não confundir com `anderzilla-web-production`/anderzilla.com, que não foi tocado aqui.
- **Não verificado nesta entrega:** conteúdo renderizado real dentro do homolog. Sem acesso de revisor autenticado disponível nesta sessão (mesmo bloqueio de OAuth/convite descrito em `AZURE-RELEASE.md`), não foi possível abrir o site logado para conferir visualmente as páginas publicadas. Revisão visual pelo proprietário com o papel `anderzilla_reviewer` ainda é necessária antes de promover a produção.

## Correção de ferramental (achado durante este deploy)

`infra/azure/deploy.ps1`/`prepare-artifact.ps1` dependiam de `ConvertFrom-Json -AsHashtable` e `Set-Content -Encoding utf8NoBOM`, ambos exclusivos do PowerShell 7+ (`pwsh`). Esta máquina só tem Windows PowerShell 5.1 (`$PSVersionTable.PSVersion` 5.1.26100.9444) e `pwsh` não está instalado — o deploy falhava antes de tocar o Azure. Reescrito `prepare-artifact.ps1` para usar `PSCustomObject`/`Add-Member`/`PSObject.Properties.Remove` e um helper `Set-Utf8NoBom` baseado em `[System.IO.File]::WriteAllText`, compatível com 5.1 e 7 igualmente. Testado isoladamente (config resultante sem BOM, rotas/headers corretos) antes do deploy real. `identity-deploy.ps1` tem os mesmos `-Encoding utf8NoBOM`; ainda não corrigido porque a implantação de `services/identity` no Azure não foi executada nesta sessão.

## Reproduzir

```powershell
$env:AZURE_CONFIG_DIR='C:/Users/ander/.codex/anderzilla-azure'
cd Z:/AnderZilla
npm --prefix apps/web run build
./infra/azure/deploy.ps1 -Environment homolog -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
```

Não usar `2>&1` ao redor da chamada no Windows PowerShell 5.1: a saída de progresso do `node`/SWA CLI vem por stderr e um redirecionamento aqui vira `NativeCommandError` mesmo com o deploy bem-sucedido (visto nesta sessão).
