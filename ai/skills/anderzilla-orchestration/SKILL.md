---
name: anderzilla-orchestration
description: Projetar e revisar processos Azure/Google controlados pelo CMS AnderZilla, contratos de eventos e recuperação.
---

# anderzilla-orchestration

Aplicar apenas AnderZilla. Fonte canônica Z:/AnderZilla-docs, branch codex/anderzilla-docs.

Leia strategy/INTEGRATED-AUTOMATION-ROADMAP.md e strategy/AUTOMATION-CMS-CONTROL.md. CMS é autoridade; use outbox/inbox, IDs idempotentes e transições versionadas. Diferencie agentes de desenvolvimento de workers runtime. Valide autorização, replay, cancelamento, quota e falha parcial. Não acople disponibilidade pública ao Google. planner.py gera planos locais, nunca prova execução cloud.

Relatar claramente o que foi preparado, testado e implantado. Código runtime pertence ao worktree Z:/AnderZilla; documentação e ferramentas IA ficam aqui.
