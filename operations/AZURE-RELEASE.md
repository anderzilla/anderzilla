# Azure — publicação do portal

## Estado em 10/09/2026

Azure é o destino principal autorizado. Login CLI e portal confirmados como anderzilla@ymail.com, tenant 3fdcb773-0842-4fb9-925e-bea17d681f83, assinatura ativa 44b76346-26bd-4cd3-a529-627e47e99e5a. Grupo anderzilla-web, região eastus2, provider Microsoft.Web registrado. Somente duas Static Web Apps **SKU Free**, sem backend, banco, Front Door ou plano pago.

| Ambiente | Recurso | URL | Resultado |
|---|---|---|---|
| Homolog | anderzilla-web-homolog | https://salmon-stone-0a4d29c0f.5.azurestaticapps.net | Publicado; requisição anônima retorna401. Conteúdo exige papel anderzilla_reviewer. |
| Produção | anderzilla-web-production | https://mango-coast-0322c590f.5.azurestaticapps.net | Publicado e inspecionado no Chrome. Home/ForgeKit/StackPick/comparativo/links/sitemap/OG retornaram200, caminho inexistente404. |

O acesso autenticado do proprietário em homolog ainda precisa ser concluído: houve consentimento Microsoft de perfil/email, mas o retorno identity.5.azurestaticapps.net foi bloqueado pelo Chrome (ERR_BLOCKED_BY_CLIENT), e recarregar o nonce consumido retorna401. Isso é distinto do login administrativo Azure, que funciona. Convite para conta ymail e papel específico foi criado, mas não declarar aceitação/validação visual privada sem confirmação. Nenhuma informação privada foi publicada: o conteúdo é o mesmo portal público.

## Domínio e email

DNS Wix alterado e conferido no servidor autoritativo:

- anderzilla.com A -> **20.22.16.164**, propriedade stableInboundIP obtida pela API ARM2024-11-01.
- www.anderzilla.com CNAME -> **mango-coast-0322c590f.5.azurestaticapps.net**.
- Removidos os dois A legados restantes da Wix; backup em DNS-ROLLBACK.md.
- TXT de validação Azure adicionado na raiz e em _dnsauth.www (validação do subdomínio). Ambos conferidos no DNS autoritativo. TXT Google e SPF preservados.
- Cinco MX Google e nameservers Wix preservados e reconsultados após alterações.

Às 05:57 UTC, anderzilla.com está Ready no Azure e responde HTTP200 com certificado HTTPS válido ao consultar diretamente 20.22.16.164 usando SNI anderzilla.com (curl --resolve, sem ignorar TLS). O resolvedor local ainda devolve Wix por cache; a propagação não é instantânea. www ainda está Validating e seu certificado não foi confirmado; TXT _dnsauth.www foi acrescentado para concluir a validação pendente. A URL Azure permanece disponível durante propagação.

A Wix não oferece ALIAS neste painel; A usa host regional, enquanto CNAME www mantém resolução pelo hostname Azure. Não foi contratado Azure DNS nem transferido o domínio.

## Build e entrega

apps/web exporta estático por padrão. `npm run build` passou e gerou70 arquivos, 12 rotas no sitemap e OG PNG1200x630. Manifesto SHA256 em AZURE-ARTIFACT.json: 5393f7676628dbf29cea38537703bf31f2c30861d94e45859c9b519305477fd1. Docker preserva opção NEXT_OUTPUT=standalone. ForgeKit funcional não foi alterado nesta migração; a demo Cloud Run continua existente.

Scripts de código:

- infra/azure/prepare-artifact.ps1: copia o build; homolog acrescenta ACL de papel convidado, noindex e no-store. Produção preserva bytes da configuração pública.
- infra/azure/deploy.ps1: verifica conta/tenant/assinatura/SKU Free e publica apenas app existente. Captura token sem imprimir, usa variável temporária e limpa staging próprio. **Fixa app-location e swa-config-location no staging** para impedir descoberta da configuração pública pelo CLI durante deploy privado.
- .github/workflows/deploy-azure-web.yml: build em develop, smoke de proteção privada, artefato imutável e promoção manual em main com verificação da origem.

A primeira tentativa CLI encontrou configuração pública no repositório; isso foi corrigido com diretórios explícitos e homolog foi republicado. Só a versão final teve teste401 aprovado. Não copiar o padrão de descoberta automática.

## Operação local

Azure CLI2.90.0 portátil: C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd. Configuração isolada em C:/Users/ander/.codex/anderzilla-azure. SWA CLI2.0.10. Não versionar tokens/cache nem imprimir saída de secrets list.

```powershell
$env:AZURE_CONFIG_DIR='C:/Users/ander/.codex/anderzilla-azure'
./infra/azure/deploy.ps1 -Environment homolog -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
# Após revisão do artefato:
./infra/azure/deploy.ps1 -Environment production -AzureCli 'C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
```

## Pipeline remoto e pendências

Workflow preparado e YAML validado, ainda não executado no GitHub. Consulta confirmou repositório privado, Actions habilitado e permissões admin, mas nenhuma branch remota/environment. O plano da conta não foi informado pela API; recursos de proteção para repositório privado precisam ser confirmados. Não apresentar o workflow como CI/CD remoto ativo.

Antes de automatizar: publicar branches pelo fluxo acordado, configurar tokens distintos em environments homolog/production e verificar as proteções disponíveis no plano. Não fazer squash que elimine a ancestralidade do commit homologado usada pela promoção. O workflow GCP foi arquivado em infra/gcp/deploy-web.workflow.yml e saiu da pasta de workflows ativos.

GCP criado anteriormente permanece sem novo deploy/faturamento vinculado por esta execução. Google Workspace continua responsável pelo email. Assinatura Workspace não equivale a crédito para consumo GCP.
