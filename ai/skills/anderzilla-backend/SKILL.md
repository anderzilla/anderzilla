---
name: anderzilla-backend
description: Projetar e implementar APIs, banco, pontos e resgates AnderZilla com integridade transacional. Usar somente no projeto AnderZilla.
---

# AnderZilla backend

Documentação canônica neste computador: Z:/AnderZilla-docs, branch codex/anderzilla-docs; em outra máquina localizar o worktree fixado por .anderzilla-docs-ref.

Leia strategy/KARACA-POINTS.md e a arquitetura backend vigente. Identidade, saldo, estoque e elegibilidade são autoritativos no servidor. Exija idempotência, transações e auditoria nos comandos de recompensa; não use localStorage como evidência. Não crie serviços pagos por mera sugestão técnica. Trabalhe nos arquivos delegados e teste concorrência, replay e autorização entre contas. Relate infraestrutura proposta separada da implantada.

Consulte a versão documental e instruções do repositório antes de implementar. Não copie dossiê nem ferramentas de IA para o código. Mudanças em apps exigem npm run build. Se alguma integração estiver apenas preparada, descreva assim no resultado.
