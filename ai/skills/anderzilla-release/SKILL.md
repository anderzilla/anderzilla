---
name: anderzilla-release
description: Preparar, validar e executar releases AnderZilla em homologação e produção com a conta correta e orçamento definido.
---

# anderzilla-release

Documentação canônica neste computador: `Z:/AnderZilla-docs`, branch `codex/anderzilla-docs`. Em outra máquina use o worktree fixado por `.anderzilla-docs-ref`. Aplicar somente ao projeto AnderZilla.

Leia operations/ACCESS-INVENTORY.md, operations/AZURE-RELEASE.md e .anderzilla-docs-ref. Execute npm run build nas apps tocadas e verificações relevantes. Publicar o export estático apps/web/out; não ativar backend híbrido por acidente. Infra validada não é deploy concluído: registrar revisão, artefato, URL, smoke check e rollback após publicação real.

Cloud Run é legado: se solicitado, consultar operations/CLOUD-RUN-RUNBOOK.md e usar configuração anderzilla com projeto explícito confirmado, preservando recursos CodeMatrix. Não reativar fluxo GCP para o portal por orientação histórica.

## Direção atual
O proprietário escolheu Azure como hospedagem principal. Para o portal, seguir decisions/AZURE-PRIMARY.md e operations/AZURE-RELEASE.md; Cloud Run é histórico/legado. Validar SKU Free e assinatura 44b76346-26bd-4cd3-a529-627e47e99e5a, tenant 3fdcb773-0842-4fb9-925e-bea17d681f83, identidade anderzilla@ymail.com. Preservar DNS de email Google. A autorização atual inclui publicação do portal e apontamento do domínio, portanto não pedir autorização novamente para esses passos.
