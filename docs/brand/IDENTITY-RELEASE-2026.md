# AnderZilla - nova identidade visual

Atualização preparada em 27/10/2026 a partir da branch de aplicação `codex/anderzilla-foundation`, commit `f4a2e7c6216e38ada16df41a17408b4ccb79ee44`.

## Escopo

- Lettering aprovado no header e no rodapé, incluindo comércio, páginas legais, páginas editoriais e shell legado.
- Caveira aprovada na abertura; avatar e versão reduzida nas interfaces da comunidade.
- Fundo azul escuro #080D19 preservado; acentos quentes derivados da marca.
- Favicons SVG/ICO/PNG, Apple Touch e cartão social 1200 x 630.
- WebP derivados dos originais do Kit_AnderZilla_2026. Proporções preservadas; sem recriação do lettering.
- Sem alteração de catálogos, preços, artigos, contas, regras comerciais, DNS ou infraestrutura.

## Verificação

`npm ci --ignore-scripts --no-audit --no-fund` e `npm run build` concluídos nesta sessão Linux. Compilação, checagem de tipos e exportação de 54 páginas estáticas aprovadas.

Revisão visual no navegador ainda deve ser concluída: o navegador remoto não conseguiu acessar o servidor local. Conferir larguras 320, 375, 768, 1100 e 1440 px, PT/EN, navegação, conta, logo, ícones e preview social em homolog.

## Preservação editorial obrigatória

A produção foi inspecionada em https://anderzilla.com/ nesta sessão e exibe 60 descobertas. O fonte remoto compilado usa o snapshot de conteúdo versionado e gera 54 páginas; o build aprovado verifica o código visual, não a atualização do corpus editorial. Antes de qualquer deploy, recuperar o corpus de produção pelo processo de publicação vigente, preservar as 60 descobertas, os slugs PT/EN e todas as mídias. Conferir o sitemap e os links antes/depois. Não publicar diretamente a exportação parcial desta sessão.

## Publicação existente

O portal usa Azure Static Web Apps Free, recursos `anderzilla-web-homolog` e `anderzilla-web-production`, grupo `anderzilla-web`. O deploy existente está em `infra/azure/deploy.ps1` e valida a identidade, assinatura e SKU antes de publicar.

Os workflows do repositório não têm execuções registradas. Não presumir uma esteira de publicação ativa apenas pela existência dos YAMLs.

No computador com a sessão Azure autorizada, o checkout completo desta branch, o worktree documental e o artefato editorial vigente:

```powershell
$env:AZURE_CONFIG_DIR='C:/Users/ander/.codex/anderzilla-azure'
python infra/azure/rebuild-production.py
if ($LASTEXITCODE -ne 0) { throw 'Baseline editorial não verificada; interromper publicação' }
python infra/azure/rebuild-production.py --build --output-name production-brand-20261027
if ($LASTEXITCODE -ne 0) { throw 'Falha ao preservar corpus e mídias; interromper publicação' }
./infra/azure/deploy.ps1 -Environment homolog -ArtifactPath '.deploy/production-brand-20261027' -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
```

Conferir homolog e, após a validação do mesmo artefato:

```powershell
./infra/azure/deploy.ps1 -Environment production -ArtifactPath '.deploy/production-brand-20261027' -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
```

Usar sempre ArtifactPath explícito para o artefato reconstruído e validado. Não publicar apps/web/out obtido apenas do snapshot versionado. O script de reconstrução faz preflight e falha se corpus/mídias não estiverem disponíveis ou divergirem do baseline.

A publicação deve ser seguida por smoke tests de HTTPS, 60 descobertas, 120 páginas editoriais PT/EN, mídias preservadas, favicon e assets /brand. Não alterar DNS.

## Estado desta preparação

Fonte remoto e kit aprovados recuperados, nova identidade integrada e build aprovado. A sessão Azure do Windows não está disponível no ambiente Linux desta conversa; o portal Azure apresenta login. Nenhuma publicação foi executada por esta preparação.

Os PNGs legados do repositório permanecem intocados na branch remota. O deploy deve usar um checkout completo e o build correspondente, nunca uma pasta parcial de arquivos obtidos por API.

## Reversão

Reverter o commit da identidade e publicar o artefato resultante pelo script existente, sem apagar os arquivos legados de `public/hub`.

