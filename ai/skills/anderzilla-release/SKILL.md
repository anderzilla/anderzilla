---
name: anderzilla-release
description: Preparar, validar e executar releases AnderZilla em homologação e produção com a conta correta e orçamento definido.
---

# anderzilla-release

Documentação canônica neste computador: `Z:/AnderZilla-docs`, branch `codex/anderzilla-docs`. Em outra máquina use o worktree fixado por `.anderzilla-docs-ref`. Aplicar somente ao projeto AnderZilla.

Leia operations/ACCESS-INVENTORY.md, operations/CLOUD-RUN-RUNBOOK.md e .anderzilla-docs-ref. Trate scripts antigos de deploy sem projeto/identidade explícitos como não utilizáveis.
Para Google Cloud, use configuração anderzilla e conta player.one@anderzilla.com; selecione projetos AnderZilla confirmados, nunca o default da máquina. Valide o plano de infraestrutura, faturamento e quota. Ambiente homolog privado; produção só com artefato validado, identidade de publicação e custo cobertos pela autorização.
Execute npm run build em apps tocadas e verificações relevantes. Infra declarativa validada não é deploy concluído: registrar revisão, digest, URL, smoke check e rollback após publicação real. Azure só se assinatura e benefício forem comprovados e resolverem necessidade; não duplicar produção por disponibilidade de conta.

## Direção atual
O proprietário escolheu Azure como hospedagem principal. Para o portal, seguir decisions/AZURE-PRIMARY.md e operations/AZURE-RELEASE.md; Cloud Run é histórico/legado. Validar SKU Free e assinatura 44b76346-26bd-4cd3-a529-627e47e99e5a, tenant 3fdcb773-0842-4fb9-925e-bea17d681f83, identidade anderzilla@ymail.com. Preservar DNS de email Google. A autorização atual inclui publicação do portal e apontamento do domínio, portanto não pedir autorização novamente para esses passos.
