# Decisão: Azure como hospedagem principal

O proprietário autorizou publicar AnderZilla no Azure e direcionar anderzilla.com, preservando Google para serviços úteis efetivamente incluídos. A decisão substitui a preferência anterior por Cloud Run.

O portal usa exportação Next.js estática e Azure Static Web Apps SKU Free. Homologação e produção são apps separadas no grupo anderzilla-web. Homolog exige papel específico de revisor convidado; autenticação genérica não concede acesso. A produção mantém conteúdo idêntico, mudando apenas política de acesso da configuração de entrega. O servidor ForgeKit legado não é migrado nesta etapa, pois autenticação e SQLite requerem decisão de persistência.

DNS permanece na Wix, sem transferência de domínio ou nameservers. Alterar apenas A/CNAME web e adicionar TXT de validação Azure; preservar MX Google, SPF e TXT existente. O plano gratuito não tem SLA e possui franquia de tráfego; não habilitar Front Door, backend ou plano pago automaticamente.

Fontes: [SWA Free e preços](https://azure.microsoft.com/en-us/pricing/details/app-service/static/), [domínio raiz externo](https://learn.microsoft.com/en-us/azure/static-web-apps/apex-domain-external), [autorização e roles](https://learn.microsoft.com/en-us/azure/static-web-apps/authentication-authorization).

Credenciais CLI ficam em C:/Users/ander/.codex/anderzilla-azure, fora do Git. Tokens de deploy são capturados em memória e nunca registrados. O workflow GCP foi retirado de .github/workflows e arquivado em infra/gcp/deploy-web.workflow.yml para referência.

Estado da execução e endereços reais ficam em operations/AZURE-RELEASE.md.
