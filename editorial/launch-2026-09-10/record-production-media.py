import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('Z:/AnderZilla');DOCS=Path('Z:/AnderZilla-docs')
DATA=Path(__file__).resolve().parent/'real-media-2026-09-16'
receipt=json.loads((DATA/'production-release.json').read_text())
assert receipt['status']=='deployed-and-verified' and receipt['artifact'].endswith('-launch')
artifact=Path(receipt['artifact'])
files={str(path.relative_to(artifact)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(artifact.rglob('*')) if path.is_file()}
(DATA/'production-artifact-sha256.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
patch=subprocess.check_output(['git','diff','--binary'],cwd=ROOT,stderr=subprocess.DEVNULL)
(DATA/'production-working-tree.patch').write_bytes(patch)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
text=f'''# Publicação editorial em produção — 16/09/2026

Confirmada em {receipt['verifiedAt']} em https://anderzilla.com e https://www.anderzilla.com.

- Azure Static Web Apps Free: anderzilla-web-production; identidade, assinatura e tenant conferidos pelo script de deploy. DNS e email preservados.
- Snapshot CMS `{receipt['releaseId']}`, SHA256 `{receipt['snapshotSha256']}`. 60 matérias PT/EN, 50 capas das fontes, 35 galerias e 10 alternativas editoriais.
- Build de 138 páginas aprovado; 120 páginas de artigos conferidas byte a byte contra o artefato publicado; 242 URLs de imagens/previews responderam HTTP 200.
- Robots permite indexação, sitemap inclui as 120 URLs editoriais, HTTPS válido nos dois domínios e rota inexistente retorna 404.
- Inspeção no navegador confirmou fotos, créditos, metadados sociais e cabeçalho sem o antigo rótulo de prévia. Avisos de pontos demonstrativos preservados.
- Código base `{revision}` mais alterações locais preservadas em `production-working-tree.patch` (SHA256 `{hashlib.sha256(patch).hexdigest()}`), no diretório editorial real-media-2026-09-16.
- Artefato imutável: `{artifact}`. Manifesto: `production-artifact-sha256.json` no mesmo diretório editorial.

## Rollback

Versão pública anterior salva em `{receipt['rollbackArtifact']}`: 70 arquivos conferidos contra AZURE-ARTIFACT.json antes da publicação.

Para restaurar, executar `infra/azure/deploy.ps1 -Environment production -ArtifactPath '{receipt['rollbackArtifact']}' -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'`, com AZURE_CONFIG_DIR=C:/Users/ander/.codex/anderzilla-azure. Conferir HTTPS e páginas após o deploy. Não alterar DNS.

As revisões das matérias e mídias permanecem no CMS. A promoção reutiliza o snapshot aprovado; não cria notícias duplicadas nem muda o estado da prévia visual.
'''
(DOCS/'operations/AZURE-EDITORIAL-PRODUCTION-2026-09-16.md').write_text(text,encoding='utf-8')
runbook=DOCS/'operations/AZURE-RELEASE.md'
with runbook.open('a',encoding='utf-8') as output:
    output.write('\n\n## Atualização — lançamento editorial em produção, 16/09/2026\n\n60 matérias e imagens revisadas publicadas no domínio oficial. HTTPS, 120 páginas PT/EN, 242 arquivos de mídia e indexação verificados. Registro e rollback: [AZURE-EDITORIAL-PRODUCTION-2026-09-16.md](AZURE-EDITORIAL-PRODUCTION-2026-09-16.md).\n')
print(json.dumps({'record':'operations/AZURE-EDITORIAL-PRODUCTION-2026-09-16.md','artifactFiles':len(files),'revision':revision}))
