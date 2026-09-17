# Execução consolidada — 17/09/2026

Inventário dos **33 documentos** em `Z:/AnderZilla-docs/strategy`, cruzado com o espelho `docs/` e código local. Fotografia anterior à nova implementação de contas. A solicitação atual autoriza execução e produção; os requisitos de evidência, orçamento e integrações continuam critérios de aceite, não novas solicitações genéricas de permissão.

Espelho conferido por hash: 14 dos 15 nomes comuns são idênticos; `BRIEF-trust-commerce-copy-br-intl.md` difere apenas na referência relativa ao anexo (`docs/` versus `strategy/`). Não há divergência de escopo nos briefs de auth.

## Inventário completo, sem repetir briefs

| Frente / documentos (nomes sem `.md`) | Estado e próxima entrega |
|---|---|
| `BRAND-AND-PRODUCT`, `BRAND-MANUAL`, `EDITORIAL-TEMPLATE`, `HUB-GAMIFICATION`, `NEXTJS-IMPLEMENTATION` | Referências de identidade e arquitetura; hub React existe. Template editorial inicial foi substituído. Preservar Ghost, PT/EN, acessibilidade e navegação pública. |
| `TRUST-AND-COMMERCE-CMS`, `TRUST-AND-COMMERCE-CMS-PROMPT`, `BRIEF-trust-commerce-br-intl`, `BRIEF-trust-commerce-cms-market`, `BRIEF-trust-commerce-copy-br-intl`, `BRIEF-trust-commerce-live-karaca`, `LOAD-SPLIT-trust-commerce` | Uma entrega: rotas e sete coleções implementadas nesta sessão; validar artefato, cadastrar ForgeKit aprovado antes de substituir snapshot legado e promover o mesmo conteúdo homologado. Guia: `docs/TRUST-COMMERCE-EDITOR-GUIDE.md`. |
| `CANDIDATES-AFFILIATES-BR`, `SPONSOR-KIT-DRAFT`, `MONETIZATION-PROCESS-REGISTER` | Candidatos/kit/registro; aprovação, contrato e tracking não são comprovados por código. Atualizar evidência de cada processo. |
| `BRIEF-auth-karaca-accounts`, `BRIEF-auth-gap-analysis`, `BRIEF-auth-legal-security`, `BRIEF-auth-backend-ledger`, `BRIEF-auth-ui-ux`, `LOAD-SPLIT-auth-karaca` | Uma entrega nova. Gap: `AUTH-PERSONALIZATION-GAP.md`. Contas de visitante, verificação, Google, perfil e ledger precisam de integração real. |
| `BACKEND-AND-DATA`, `ADMIN-CMS-PLAN`, `CMS-UX-AUDIT` | CMS operacional parcial; rewards é referência local. Revalidar achados antigos antes de corrigi-los novamente; mídia/SEO/publicação já avançaram. |
| `KARACA-POINTS`, `KARACA-ECONOMY-AND-PARTNERSHIPS` | Demo existente; economia, XP, financiamento, catálogo e fornecimento são evolução separada. Sem migração automática de saldo. |
| `AUTOMATION-CMS-CONTROL`, `INTEGRATED-AUTOMATION-ROADMAP`, `CROSS-CLOUD-SEO` | Controle/worker parciais. Próximo fluxo: fonte real → rascunho → revisão → publisher; depois cortes, relatórios conciliados e recuperação. |
| `EDITORIAL-90-DAYS`, `HUB-LIVE-AND-MONETIZATION` | Pautas e superfícies existem; produção editorial, direitos, agenda e status live exigem fatos reais. |
| `ROADMAP`, `ROTEIRO-TORNAR-REAL` | Orquestração; não executar duas vezes entregas incluídas acima. ROADMAP contém hosting histórico supersedido. |

## Ordem e critérios

1. **Contrato/gap:** separar conta visitante de Entra/CMS e ForgeKit. O novo brief email+Google substitui a proposta antiga GitHub/Microsoft. Azure SWA prevalece sobre GCP principal descrito no ROADMAP.
2. **Legal + backend paralelos:** páginas PT/EN e consentimento; identidade, sessões, verificação, perfil, revogação/exclusão/exportação; ledger idempotente e evidência de missão no servidor. Dependências externas: cliente Google/callbacks, envio de email, armazenamento Azure durável; Instagram fica indisponível até viabilidade oficial comprovada.
3. **UI integrada:** preservar preferências anônimas; modal de convite, perfil e sincronização. Testar expiração, replay, conta não verificada, isolamento entre contas e indisponibilidade sem saldo demo substituto.
4. **Homolog → produção autorizada:** builds, testes, QA PT/EN 320–1440px, autenticação real, migração aditiva, backup/rollback, URLs e revisão publicada comprovados. Não promover implementação parcial como login funcional.
5. **Operação:** ativar somente integrações comprovadas. Contratos/estoque/verba antecedem resgates; direitos/custo por minuto antecedem cortes; fontes conciliadas antecedem receita reportada. PartnerStack: reaplicação somente a partir de 21/09/2026.

## IAs verificadas

`Get-Command` e `--version`: Claude Code **2.1.215** (`C:/Users/ander/.local/bin/claude.exe`) e Codex CLI **0.155.0-alpha.2.6** (diretório OpenAI/Codex em AppData). Gemini, Copilot e Ollama não resolveram no PATH. Isso comprova binários, não sessão, assinatura ou quota. Não foram lidas credenciais nem dados de outros projetos. Delegar arquivos exclusivos; registrar o provedor efetivamente executado e revisar integração uma vez.
