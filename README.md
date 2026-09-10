# AnderZilla — documentação e operação

Esta branch contém a estratégia, o inventário, as decisões e as ferramentas de IA do AnderZilla. O código de produto está na branch de desenvolvimento do mesmo repositório, em outro worktree.

Comece pelo [dossiê](DOSSIER.md), pelo [estado dos acessos](operations/ACCESS-INVENTORY.md) e pelo [plano por fases](strategy/ROADMAP.md).

## Mapa
- [Direção de marca e produto](strategy/BRAND-AND-PRODUCT.md)
- [Pesquisa de monetização](research/monetization.md)
- [Presença pública, jogos e contas](research/gaming-presence.md)
- [Revisão independente de arquitetura](research/architecture-review.md)
- [Debate entre IAs e decisões](decisions/AI-REVIEW.md)
- [Plano editorial de 90 dias](strategy/EDITORIAL-90-DAYS.md)
- [Rascunho para patrocinadores](strategy/SPONSOR-KIT-DRAFT.md)
- [Fluxo de branches e versões](operations/DEVELOPMENT-FLOW.md)
- [Operação de agentes, skills e MCP](ai/OPERATING-MODEL.md)
- [RAG local](ai/rag/README.md)

## Uso das branches
- Documentação canônica: `codex/anderzilla-docs`, worktree `Z:/AnderZilla-docs`.
- Implementação atual: `codex/anderzilla-foundation`, worktree `Z:/AnderZilla`.
- Fluxo de produto planejado: feature -> PR -> develop/homologação -> main/produção.
- Não fazer merge desta branch órfã na branch de aplicação. Registrar seu commit em `.anderzilla-docs-ref` no código.
- `archive/initial` guarda contexto anterior, substituído pela direção atual. Não é entrada do RAG.
- `private/` e `.cache/` ficam fora do Git e do índice de conhecimento.

Os relatórios distinguem observação autenticada, informação do proprietário, fonte pública e hipótese. Uma integração listada não está automaticamente conectada; uma configuração de deploy validada não significa ambiente publicado.
